import sys
from subprocess import check_call, run, PIPE
import os
import shutil
from kern_util import *

dryrun = False
kern_version = None
kern_type = None
if len(sys.argv) < 2:
    print('No build command given, building mainline kernel')
else:
    # example input: 4.10.1: stable
    print('Parsing build command: {0}'.format(sys.argv[1]))
    kern_version, kern_type = map(str.strip, sys.argv[1].split(':'))  # '4.10.1', stable

    if len(sys.argv) > 2:
        if sys.argv[2] == '--dryrun':
            dryrun = True
            print('DRYRUN')

if kern_type is None:
    kern_type = 'mainline'

print('Building kernel type: {}'.format(kern_type))

if not dryrun:
    check_call(['git', 'clone', kern_urls[kern_type], 'linux'])

    if kern_version is None:
        os.chdir('linux')
        kern_version = run(['git', 'describe', 'master', '--abbrev=0'], stdout=PIPE).stdout.decode('utf-8').strip()[1:]
        os.chdir('..')

print('Got kernel version: {0}'.format(kern_version))

kern_vl = kern_version.split('.')  # 4, 10, 1
kern_maj = kern_vl[0]
kern_min = kern_vl[1]
kern_patch = kern_vl[2] if len(kern_vl) > 2 else None

if '-' in kern_min:
    kern_min, kern_rc = kern_min.split('-')
else:
    kern_rc = None

print('Major: {0}, Minor: {1}, Patch: {2}, RC: {3}'.format(kern_maj, kern_min, kern_patch, kern_rc))

if kern_patch is not None:
    kern_tag = 'v{0}.{1}.{2}'.format(kern_maj, kern_min, kern_patch)
elif kern_rc is not None:
    kern_tag = 'v{0}.{1}-{2}'.format(kern_maj, kern_min, kern_rc)
else:
    kern_tag = 'v{0}.{1}'.format(kern_maj, kern_min)

# Checkout kernel
acso_tag = find_tag(kern_maj, kern_min, kern_patch, kern_rc)

if not dryrun:
    os.chdir(acso_tag)
if not dryrun:
    check_call(['git', 'checkout', kern_tag])

# Checkout patch
if not dryrun:
    os.chdir('linux')

if not dryrun:
    os.chdir('..')

# Apply patch
if not dryrun:
    os.chdir('linux')
    check_call(['git', 'apply', '../acso.patch'])
    check_call(['git', 'apply', '../build.patch'])

print('ready to build')

