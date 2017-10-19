import sys
from subprocess import check_call
import os
import shutil
import kern_util
import argparse
import glob


def select_workspace(major, minor, patch, rc, **kwargs):
    def format_tag(kspec_partial):
        ks = kern_util.format_kernel(kspec_partial)
        return '{}*'.format(ks)

    def look_for(ver):
        return [d for d in glob.glob(ver) if os.path.isdir(d)]

    def match_exact(major=None, minor=None, patch=None, rc=None):
        kspec = kern_util.kernel_spec(major, minor, patch, rc)
        target_tag = format_tag(kspec)
        tag_found = look_for(target_tag)

        if tag_found != '':
            return True, tag_found, target_tag
        else:
            return False, None, target_tag

    def match_leq(major=None, minor=None):
        kspec = kern_util.kernel_spec(major=major)
        target_ws = format_tag(kspec)
        workspaces = look_for(target_ws)

        if len(workspaces) > 0:
            workspaces.sort()
            workspaces.reverse()

            for ws in workspaces:
                if major is not None:
                    target = minor
                    query = ws.split('.')[1] if '.' in ws else None
                else:
                    target = major
                    query = ws.split('.')[0] if '.' in ws else ws
                    query = query[1:]

                if query is not None:
                    if int(query) <= int(target):
                        return True, ws, target_ws

        return False, None, target_ws

    # step 1: try to find a workspace for the specific kernel and patch
    if patch is not None:
        found, workspace, target = match_exact(major=major, minor=minor, patch=patch)
        if found:
            print('Found exact match for {0}'.format(target))
            return workspace
        else:
            print('No matching patch for {0}'.format(target))

    # step 2: try to find a workspace for the kernel maj, min, and rc
    if rc is not None:
        found, workspace, target = match_exact(major=major, minor=minor, rc=rc)
        if found:
            print('Found exact match {0} for {1}'.format(workspace, target))
            return workspace
        else:
            print('No matching rc for {0}'.format(target))

    # step 3: try to find a workspace for the kernel maj and min version
    found, workspace, target = match_exact(major=major, minor=minor)
    if found:
        print('Found exact match {0} for {1}'.format(workspace, target))
        return workspace
    else:
        print('No matching minor version for {0}'.format(target))

    # step 4: try to build from closest workspace less than minor version
    found, workspace, target = match_leq(major=major, minor=minor)
    if found:
        print('Using {0} as closest minor version for {1}'.format(workspace, target))
        return workspace
    else:
        print('No matching minor version for {0}'.format(target))

    # step 5: try to build from closest workspace less than major version
    found, workspace, target = match_leq(major=major)
    if found:
        print('Using {0} as closest major version for {1}'.format(workspace, target))
        return workspace
    else:
        print('No lower versions for {0}'.format(target))

    # step 6: try to build from the latest workspace, if this fails the patches need updating
    dirs = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.')]
    dirs.sort()
    dirs.reverse()

    workspace = dirs[0]

    print('Using latest workspace: {0}'.format(workspace))
    return workspace


def main(args):
    print('Arguments: {}'.format(args))
    print('Parsing build command: {0}'.format(args.kernel_string))

    kspec = kern_util.parse_kernel(args.kernel_string)

    if args.dryrun:
        print('DRYRUN')

    print('Setting up for kernel: {}'.format(kspec))

    acso_workspace = select_workspace(**kspec)

    if not args.dryrun:
        os.chdir(acso_workspace)
        kern_util.download_kernel_source(kspec)
        os.chdir('linux')

    kern_tag = 'v{}'.format(kern_util.format_kernel(kspec))
    print('Checking out kernel tag {}'.format(kern_tag))

    # Apply patchs
    if not args.dryrun:
        check_call(['git', 'checkout', kern_tag])

        print('Patching kernel')
        check_call(['git', 'apply', '../acso.patch'])
        check_call(['git', 'apply', '../build.patch'])

    print('ready to build')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Auto patch the kernel with the correct ACSO and build patches')
    parser.add_argument('--dryrun', action='store_true', help='Only simulate the patch selection process')
    parser.add_argument('kernel_string', help='String description, <kernel_number>:[mainline|stable]')
    args = parser.parse_args()
    main(args);