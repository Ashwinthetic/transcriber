import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

r = urllib.request.urlopen('http://127.0.0.1:8000/', timeout=10)
print('Root:', r.status)
content = r.read().decode('utf-8')
print('Frontend loaded:', 'Voice Input Studio' in content)
print('Lang select has hn:', 'value="hn"' in content)