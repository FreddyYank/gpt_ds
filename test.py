import json

import os




files = []

for file in os.listdir('.requests/'):
    files.append(file)
name = 'Fred.json'
if name not in files:
    response0 = {
        'user':[{"role": "user", "content": [{"type": "text", "text": 'Hi'}]},],
        'assistant':[{"role": "user", "content": [{"type": "text", "text": 'Hi'}]},]
    }

    with open('.requests/Fred.json', 'w') as f:
        json.dump(response0,f)

else:
    with open('.requests/Fred.json') as f:
        templates = json.load(f)

    print(templates['user'])
