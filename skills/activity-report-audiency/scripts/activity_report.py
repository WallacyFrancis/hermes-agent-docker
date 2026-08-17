#!/usr/bin/env python3
"""Build a persistent, daily activity diff from Audiency support tickets."""
import argparse, importlib.util, json, subprocess, sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

STATE = Path('/opt/data/reports/audiency-activity-state.json')
TZ = ZoneInfo('America/Sao_Paulo')
PEOPLE = {3330: 'Wallacy', 4435: 'Henrique', 2918: 'Julia'}
SUPPORT_SCRIPT = '/opt/data/skills/suporte-audiency/scripts/suporte_audiency.py'

def client():
    spec = importlib.util.spec_from_file_location('support_client', SUPPORT_SCRIPT)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    value = module.Client(); value.login(); return value
def stamp(value): return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(TZ).date()
def relevant(ticket): return bool(({ticket.get('createdById')} | set(ticket.get('assigneeIds') or [])) & PEOPLE.keys())
def compact(ticket): return {k: ticket.get(k) for k in ('id','title','status','createdAt','updatedAt','createdById','createdByName','assigneeIds','assignees')}
def owners(ticket): return [pid for pid in PEOPLE if pid in ({ticket.get('createdById')} | set(ticket.get('assigneeIds') or []))]
def status_owners(ticket):
    assigned = [pid for pid in PEOPLE if pid in set(ticket.get('assigneeIds') or [])]
    return assigned or ([ticket.get('createdById')] if ticket.get('createdById') in PEOPLE else [])
def line(action, ticket): return f'{action} cartão #{ticket["id"]} - {ticket["title"]}'
def baseline_actions(current, previous_day):
    result = {pid: [] for pid in PEOPLE}; words = {'em_desenvolvimento':'Iniciou', 'pausado':'Pausou', 'revisao':'Enviou para revisão', 'concluido':'Finalizou'}
    for ticket in current.values():
        creator = ticket.get('createdById')
        if creator in PEOPLE and ticket.get('createdAt') and stamp(ticket['createdAt']) == previous_day: result[creator].append(line('Criou', ticket)); continue
        if ticket.get('updatedAt') and stamp(ticket['updatedAt']) == previous_day and ticket.get('status') in words:
            for person in status_owners(ticket): result[person].append(line(words[ticket['status']], ticket))
    return result
def diff_actions(current, previous):
    result = {pid: [] for pid in PEOPLE}; words = {'em_desenvolvimento':'Iniciou', 'pausado':'Pausou', 'revisao':'Enviou para revisão', 'concluido':'Finalizou'}
    for ticket_id, ticket in current.items():
        old = previous.get(ticket_id)
        if old is None:
            creator = ticket.get('createdById')
            if creator in PEOPLE: result[creator].append(line('Criou', ticket))
        elif old.get('status') != ticket.get('status') and ticket.get('status') in words:
            for person in set(status_owners(ticket)) | set(status_owners(old)): result[person].append(line(words[ticket['status']], ticket))
    return result
def render(day, actions):
    lines = [f'Desenvolvimento {day:%d/%m}', '']
    for pid, name in PEOPLE.items():
        lines.append(f'- {name}:'); entries = actions[pid]
        lines.extend(f'    - {entry}' for entry in entries) if entries else lines.append('    - Sem alterações observadas em chamados.')
        lines.append('')
    return '\n'.join(lines).rstrip()
def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--preview', action='store_true'); parser.add_argument('--send', action='store_true'); parser.add_argument('--sync-state', action='store_true'); args = parser.parse_args()
    if sum((args.preview, args.send, args.sync_state)) != 1: parser.error('use exatamente um: --preview, --send ou --sync-state')
    now = datetime.now(TZ); report_day = (now - timedelta(days=1)).date(); api = client()
    all_current = {str(t['id']): compact(t) for t in api.bff('/api/chamados/tickets?includeArchived=true')}
    current = {ticket_id: ticket for ticket_id, ticket in all_current.items() if relevant(ticket)}
    previous = json.loads(STATE.read_text()) if STATE.exists() else None
    if args.sync_state:
        STATE.parent.mkdir(parents=True, exist_ok=True); STATE.write_text(json.dumps({'observedAt': now.isoformat(), 'reportDay': report_day.isoformat(), 'tickets': all_current}, ensure_ascii=False, indent=2))
        print(f'Snapshot sincronizado: {len(all_current)} cartões.'); return
    message = render(report_day, diff_actions(current, previous['tickets']) if previous else baseline_actions(current, report_day)); print(message)
    if args.send:
        try:
            subprocess.run([sys.executable, str(Path(__file__).with_name('rocket_chat.py')), 'send', '--message', f'```\n{message}\n```'], check=True)
        except subprocess.CalledProcessError:
            raise SystemExit('Relatório não enviado; snapshot não foi atualizado.')
        STATE.parent.mkdir(parents=True, exist_ok=True); STATE.write_text(json.dumps({'observedAt': now.isoformat(), 'reportDay': report_day.isoformat(), 'tickets': all_current}, ensure_ascii=False, indent=2))
    elif not previous: print('\n[Prévia: o snapshot será salvo somente após --send.]')
if __name__ == '__main__': main()
