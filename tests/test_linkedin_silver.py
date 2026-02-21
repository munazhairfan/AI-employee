import time
from pathlib import Path
import subprocess

vault_path = Path('AI_Employee_Vault')

drop_folder = vault_path / 'Drop'
drop_folder.mkdir(exist_ok=True)

test_file = drop_folder / 'test_business.txt'
test_file.write_text('New sales opportunity for AI project.')

print('Test business file created in /Drop')
print('Waiting 10 seconds for filesystem watcher to copy to Needs_Action...')
time.sleep(10)

print('Waiting 70 seconds for orchestrator to generate draft in /Pending_Approval...')
time.sleep(70)

pending_approval = vault_path / 'Pending_Approval'
draft_files = list(pending_approval.glob('LinkedIn_Draft_*.md'))

if draft_files:
    print(f'Found draft file(s): {[f.name for f in draft_files]}')
    print('Check /Pending_Approval for draft .md - approve by adding [x] to Approve checkbox and save.')
else:
    print('No draft files found yet. Check manually.')

print('Waiting 70 seconds for orchestrator to detect approval, copy to clipboard, open browser...')
time.sleep(70)

done_folder = vault_path / 'Done'
done_files = list(done_folder.glob('LinkedIn_Draft_*.md'))

if done_files:
    print(f'File moved to Done: {[f.name for f in done_files]}')
    print('Test success if browser opened and file in Done.')
else:
    print('File not in Done yet. Check manually.')

print('Cleaning up test files...')
if test_file.exists():
    test_file.unlink()

print('Test complete.')
