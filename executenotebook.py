# executenotebook.py
#!/usr/bin/env python
import json
import requests
import os
import sys
import getopt
import time


def main():
  workspace = ''
  token = ''
  clusterid = ''
  localpath = ''
  workspacepath = ''
  outfilepath = ''
  extract_output = False

  try:
    opts, args = getopt.getopt(sys.argv[1:], 'hs:t:c:lwo:x',
                                ['workspace=', 'token=', 'clusterid=', 'localpath=', 'workspacepath=', 'outfilepath=', 'extract'])
  except getopt.GetoptError:
    print(
        'executenotebook.py -s <workspace> -t <token>  -c <clusterid> -l <localpath> -w <workspacepath> -o <outfilepath>)')
    sys.exit(2)

  for opt, arg in opts:
    if opt == '-h':
      print(
          'executenotebook.py -s <workspace> -t <token> -c <clusterid> -l <localpath> -w <workspacepath> -o <outfilepath> -x <extracts-output>')
      sys.exit()
    elif opt in ('-s', '--workspace'):
        workspace = arg
    elif opt in ('-t', '--token'):
        token = arg
    elif opt in ('-c', '--clusterid'):
        clusterid = arg
    elif opt in ('-l', '--localpath'):
        localpath = arg
    elif opt in ('-w', '--workspacepath'):
        workspacepath = arg
    elif opt in ('-o', '--outfilepath'):
        outfilepath = arg
    elif opt in ('-x', '--extract'):
        extract_output = True

  print('-s is ' + workspace)
  print('-c is ' + clusterid)
  print('-l is ' + localpath)
  print('-w is ' + workspacepath)
  print('-o is ' + outfilepath)
  print('-x is ' + str(extract_output))
  # Generate array from walking local path

  notebooks = []
  for path, subdirs, files in os.walk(localpath):
    for name in files:
      fullpath = path + '/' + name

      print("Full path is {}".format(fullpath))
      # removes localpath to repo but keeps workspace path
      fullworkspacepath = workspacepath + path.replace(localpath, '')
      print("Full Workspace path is {}".format(fullworkspacepath))

      name, file_extension = os.path.splitext(fullpath)
      if file_extension.lower() in ['.scala', '.sql', '.r', '.py']:
          row = [fullpath, fullworkspacepath, 1]
          notebooks.append(row)

  # run each element in list
  for notebook in notebooks:
    nameonly = os.path.basename(notebook[0])
    workspacepath = notebook[1]

    name, file_extension = os.path.splitext(nameonly)

    # workpath removes extension
    fullworkspacepath = workspacepath + name

    print('Running job for:' + fullworkspacepath)
    values = {'run_name': name, 'existing_cluster_id': clusterid, 'timeout_seconds': 3600, 'notebook_task': {'notebook_path': fullworkspacepath}}
    
    print(values)

    resp = requests.post(workspace + '/api/2.0/jobs/runs/submit',
                          json=values, auth=("token", token))

    runjson = resp.text
    print("runjson:" + runjson)
    d = json.loads(runjson)
    runid = d['run_id']

    i=0
    waiting = True
    while waiting:
      time.sleep(10)
      jobresp = requests.get(workspace + '/api/2.0/jobs/runs/get?run_id='+str(runid),
                        json=values, auth=("token", token))
      jobjson = jobresp.text
      print("jobjson:" + jobjson)
      j = json.loads(jobjson)
      current_state = j['state']['life_cycle_state']
      runid = j['run_id']
      if current_state in ['TERMINATED', 'INTERNAL_ERROR', 'SKIPPED'] or i >= 12:
          break
      i=i+1
    
    # get extended run output with get-output
    if extract_output:
      jobresp = requests.get(workspace + '/api/2.0/jobs/runs/get-output?run_id='+str(runid),
          auth=("token", token))
      jobjson = jobresp.text
      j = json.loads(jobjson)

  #TODO: Add create filer if it's doen't exist
    if outfilepath != '':
      file = open(outfilepath + '/' +  str(runid) + '.json', 'w')
      file.write(json.dumps(j))
      file.close()

if __name__ == '__main__':
  main()