import sys
from subprocess import check_call, run, PIPE
import os

kern_urls = {
    'mainline': 'git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git',
    'stable': 'git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git'
}


def find_tag(major, minor, patch):

    def look_for(ver):
        format_tag = 'v{0}'
        tag_prop = format_tag.format(ver)
        tf = run(['git', 'tag', '-l', tag_prop], stdout=PIPE).stdout.decode('utf-8').strip()
        return tf

    # step 1: try to find a tag for the specific kernel and patch
    if patch is not None:
        format_ver = '{0}.{1}.{2}'.format(major, minor, patch)
        tag_found = look_for(format_ver)
        if tag_found != '':
            return tag_found
        else:
            print('No matching patch for {0}'.format(format_ver))

    # step 2: try to find a tag for the kernel maj and min version
    format_ver = '{0}.{1}'.format(major, minor)
    tag_found = look_for(format_ver)
    if tag_found != '':
        return tag_found
    else:
        print('No matching version for {0}'.format(format_ver))

    # step 3: try to build from the latest tag, if this fails the patches need updating
    rec_tag = run(['git', 'describe', '--abbrev=0'], stdout=PIPE).stdout.decode('utf-8').strip()
    print('Using latest tag on branch: {0}'.format(rec_tag))
    return rec_tag

kern_version = None
kern_type = None
if len(sys.argv) < 2:
    print('No build command given, building mainline kernel')
else:
    # example input: 4.10.1: stable
    print('Parsing build command: {0}'.format(sys.argv[1]))
    kern_version, kern_type = map(str.strip, sys.argv[1].split(':'))  # '4.10.1', stable

if kern_type is None:
    kern_type = 'mainline'

print('Building kernel type: {}'.format(kern_type))
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
print('Major: {0}, Minor: {1}, Patch: {2}'.format(kern_maj, kern_min, kern_patch))

if kern_patch is not None:
    kern_tag = 'v{0}.{1}.{2}'.format(kern_maj, kern_min, kern_patch)
else:
    kern_tag = 'v{0}.{1}'.format(kern_maj, kern_min)

# Checkout kernel
os.chdir('linux')
check_call(['git', 'checkout', kern_tag])

# Checkout patch
os.chdir('..')
acso_tag = find_tag(kern_maj, kern_min, kern_patch)
check_call(['git', 'checkout', acso_tag])

# Apply patch
os.chdir('linux')
check_call(['git', 'apply', '../acso.patch'])

print('ready to build')

