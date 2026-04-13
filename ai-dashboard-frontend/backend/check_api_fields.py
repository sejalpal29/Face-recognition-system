import requests

resp = requests.get('http://localhost:8000/api/get_people')
if resp.status_code == 200:
    persons = resp.json()
    if persons:
        print('First person data:')
        p = persons[0]
        print(f'  name: {p.get("name")}')
        print(f'  age: {p.get("age")}')
        print(f'  case_no: {p.get("case_no")}')
        print(f'  status: {p.get("status")}')
        print(f'  created_at: {p.get("created_at")}')
        print('')
        print('✓ All fields available from API')
else:
    print(f'Error: {resp.status_code}')
