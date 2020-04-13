import argparse
import os.path
import re

from progress.bar import Bar

STEPDEFS_HTML_PATTERN = '''
<!DOCTYPE html>
<html>
 <head>
  <meta charset="utf-8">
  <title>Stepdefs in project</title>
 </head> 
 <body>
    <h1>All step definitons in project</h1>
    {details}
 </body> 
</html>
'''


HTML_DETAILS_PATTERN = '''
<details>
   <summary><b>{stepdefFile}</b></summary>
   <ul>
   {stepdefs}
   </ul>
</details>
<br>
'''


UNUSED_STEPS_HTML_PATTERN = '''
<!DOCTYPE html>
<html>
 <head>
  <meta charset="utf-8">
  <title>Unused steps in project</title>
 </head> 
 <body>
    <h1>All unused steps in project</h1>
    <ul>
    {steps}
    <ul>
 </body> 
</html>
'''


def find_all_stepdefs(stepdefs_directory_path):
    step_defs_dict = {}
    for dirpath, dirnames, filenames in os.walk(stepdefs_directory_path):
        for filename in [f for f in filenames if f.endswith("StepDefs.java")]:
            with open(os.path.join(dirpath, filename), 'r') as file:
                steps = []
                for line in file:
                    line = line.replace("\\\\\\", "\\")
                    line = line.replace("\\\\", "\\")
                    match = re.search('(?:@Then|@Given|@When|@And|@But).*', line)
                    if match:
                        step = match.group().strip()
                        while step.endswith("+"):
                            step += next(file).strip()
                        step = step.replace('\" +\"', '')
                        step = step.replace("\\\\\\", "\\")
                        step = step.replace("\\\\", "\\")
                        steps.append(step)
            step_defs_dict[filename] = steps
    return step_defs_dict


def make_file_with_stepdefs(step_defs_dict: dict):
    details = ''
    for key in step_defs_dict.keys():
        stepdefs = ''
        for stepdef in step_defs_dict.get(key):
            stepdefs += '<li>' + stepdef
        details += HTML_DETAILS_PATTERN.format(stepdefFile=key, stepdefs=stepdefs)

    stepdefs_file = open('stepdefs.html', 'w')
    stepdefs_file.write(STEPDEFS_HTML_PATTERN.format(details=details))
    stepdefs_file.close()
    print('Success!\nSee stepdefs.html file')


def find_all_steps_in_features(step_defs_dict: dict, feature_files_directory_path):
    bar = Bar('Processing', suffix='%(percent)d%%', max=len(step_defs_dict.keys()))
    details = ''
    for key in step_defs_dict.keys():
        stepdefs = ''
        for stepdef in step_defs_dict.get(key):
            stepdefs += '<li>' + stepdef + '<br><br>'
            for dirpath, dirnames, filenames in os.walk(feature_files_directory_path):
                for filename in [f for f in filenames if f.endswith(".feature")]:
                    with open(os.path.join(dirpath, filename), 'r') as file:
                        pattern = re.search('"(.*)"', stepdef).group(1)
                        for line in file:
                            line = line.strip().replace('Given ', '').replace('When ', '').replace('Then ', '')\
                                .replace('And ', '')
                            match = re.search(pattern, line)
                            if match:
                                stepdefs += filename + '<br>' + match.group() + '<br></li><br>'
        details += HTML_DETAILS_PATTERN.format(stepdefFile=key, stepdefs=stepdefs)
        bar.next()
    bar.finish()
    steps_in_features_file = open('steps_in_features.html', 'w+')
    steps_in_features_file.write(STEPDEFS_HTML_PATTERN.format(details=details))
    steps_in_features_file.close()
    print('Success!\nSee steps_in_features.html file')


def find_all_unused_stepdefs(step_defs_dict: dict, feature_files_directory_path):
    used_steps_set = set()
    all_stepdefs_set = set()
    bar = Bar('Processing', suffix='%(percent)d%%', max=len(step_defs_dict.keys()))
    for key in step_defs_dict.keys():
        for stepdef in step_defs_dict.get(key):
            all_stepdefs_set.add(stepdef)
            step_is_used_flag = False
            for dirpath, dirnames, filenames in os.walk(feature_files_directory_path):
                for filename in [f for f in filenames if f.endswith(".feature")]:
                    with open(os.path.join(dirpath, filename), 'r') as file:
                        pattern = re.search('"(.*)"', stepdef).group(1)
                        for line in file:
                            line = line.strip().replace('Given ', '').replace('When ', '').replace('Then ', '')\
                                .replace('And ', '')
                            match = re.search(pattern, line)
                            if match:
                                used_steps_set.add(stepdef)
                                step_is_used_flag = True
                                break
                    if step_is_used_flag:
                        break
                if step_is_used_flag:
                    break
        bar.next()
    bar.finish()
    return all_stepdefs_set.difference(used_steps_set)


def make_file_with_unused_steps(unused_steps: set):
    steps = ''
    for step in unused_steps:
        steps += '<li>' + step

    unused_steps_file = open('unused_steps.html', 'w+')
    unused_steps_file.write(UNUSED_STEPS_HTML_PATTERN.format(steps=steps))
    unused_steps_file.close()
    print('Success!\nSee unused_steps.html file.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--all', dest='all_args', nargs=1, metavar='STEPDEFS_DIRECTORY', help='Find all steps')
    parser.add_argument('-f', '--features', nargs=2, dest='feature_args',
                        metavar=('STEPDEFS_DIRECTORY', 'FEATURES_DIRECTORY'), help='Find all steps with features')
    parser.add_argument('-u', '--unused', nargs=2, dest='unused_args',
                        metavar=('STEPDEFS_DIRECTORY', 'FEATURES_DIRECTORY'), help='Find all unused steps')
    args = parser.parse_args()

    if args.all_args:
        stepdefs = find_all_stepdefs(args.all_args[0])
        make_file_with_stepdefs(stepdefs)
    if args.unused_args:
        stepdefs = find_all_stepdefs(args.unused_args[0])
        unused_steps = find_all_unused_stepdefs(stepdefs, args.unused_args[1])
        make_file_with_unused_steps(unused_steps)
    if args.feature_args:
        stepdefs = find_all_stepdefs(args.feature_args[0])
        find_all_steps_in_features(stepdefs, args.feature_args[1])
