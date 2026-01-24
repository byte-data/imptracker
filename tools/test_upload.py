import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
username = 'testadmin'
password = 'pass'
email = 'testadmin@example.com'

if not User.objects.filter(username=username).exists():
    print('Creating test admin user...')
    User.objects.create_superuser(username=username, email=email, password=password)
else:
    print('Test admin exists')

c = Client()
logged = c.login(username=username, password=password)
print('Logged in:', logged)

csv_path = r'C:\Users\OMEN\Downloads\tracker_activities_test.csv'
if not os.path.exists(csv_path):
    print('CSV not found at', csv_path)
    raise SystemExit(1)

with open(csv_path, 'rb') as fh:
    resp = c.post('/uploads/upload/', {'file': fh})

print('Status code:', resp.status_code)
content = resp.content.decode('utf-8', errors='replace')
if 'Staged and ready to load' in content:
    print('Preview successful: staged file ready')
else:
    print('Preview may have issues; checking for Unknown Masters or errors')
    if 'Unknown Masters' in content:
        print('Unknown Masters detected')
    if 'error' in content.lower():
        print('Response contains "error"')

# Save response to a local file for inspection
out = 'tools/upload_preview.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(content)
print('Wrote preview HTML to', out)
print('Done')
