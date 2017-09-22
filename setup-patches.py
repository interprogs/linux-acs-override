import sys
from subprocess import check_call, run, PIPE
import os

kern_urls = {
    'mainline': 'git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git',
    'stable': 'git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git'
}


def find_tag(major, minor, patch, rc):

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

    # step 2: try to find a tag for the kernel maj, min, and rc
    if rc is not None:
        format_ver = '{0}.{1}-{2}'.format(major, minor, rc)
        tag_found = look_for(format_ver)
        if tag_found != '':
            return tag_found
        else:
            print('No matching rc version for {0}'.format(format_ver))

    # step 3: try to find a tag for the kernel maj and min version
    format_ver = '{0}.{1}'.format(major, minor)
    tag_found = look_for(format_ver)
    if tag_found != '':
        return tag_found
    else:
        print('No matching minor version for {0}'.format(format_ver))

    # step 4: try to build from closest tag less than minor version
    format_ver = '{0}.{1}'.format(major, '*')
    tag_found = look_for(format_ver)
    if tag_found != '':
        tags = tag_found.splitlines()
        tags.reverse()

        for tag in tags:
            query_minor = tag.split('.')[1] if '.' in tag else None

            if query_minor is not None:
                if int(query_minor) <= int(minor):
                    print('Using tag {0} which is closest lower minor version'.format(tag))
                    return tag
                else:
                    print('Tag {0} is too new'.format(tag))

    print('No closer tag in the {0} series'.format(major))

    # step 5: try to build from closest tag less than major version
    format_ver = '*'
    tag_found = look_for(format_ver)
    if tag_found != '':
        tags = tag_found.splitlines()
        tags.reverse()

        for tag in tags:
            query_major = tag.split('.')[0] if '.' in tag else tag
            query_major = query_major[1:]

            if int(query_major) <= int(major):
                print('Using tag {0} which is closest lower major version'.format(tag))
                return tag
            else:
                print('Tag {0} is too new'.format(tag))

    print('No closer tag for major version {0}'.format(major))

    # step 6: try to build from the latest tag, if this fails the patches need updating
    rec_tag = run(['git', 'describe', '--abbrev=0'], stdout=PIPE).stdout.decode('utf-8').strip()
    print('Using latest tag on branch: {0}'.format(rec_tag))
    return rec_tag


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
if not dryrun:
    os.chdir('linux')

if not dryrun:
    check_call(['git', 'checkout', kern_tag])

# Checkout patch
if not dryrun:
    os.chdir('..')

acso_tag = find_tag(kern_maj, kern_min, kern_patch, kern_rc)
check_call(['git', 'checkout', acso_tag])

# Apply patch
if not dryrun:
    os.chdir('linux')
    check_call(['git', 'apply', '../acso.patch'])

print('ready to build')

