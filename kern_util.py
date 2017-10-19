kern_urls = {
    'mainline': 'git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git',
    'stable': 'git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git'
}

def find_tag(major, minor, patch, rc):

    def format_tag(major=None, minor=None, patch=None, rc=None):
        format = ''

        if major is not None:
            format = '{0}{1}'.format(format, major)

            if minor is not None:
                format = '{0}.{1}'.format(format, minor)

                if patch is not None:
                    format = '{0}.{1}'.format(format, patch)
                elif rc is not None:
                    format = '{0}-{1}'.format(format, rc)

        return '{0}*'.format(format)

    def look_for(ver):
        tf = run(['git', 'tag', '-l', ver], stdout=PIPE).stdout.decode('utf-8').strip()
        return tf

    def match_exact(major=None, minor=None, patch=None, rc=None):
        target_tag = format_tag(major, minor, patch, rc)
        tag_found = look_for(target_tag)

        if tag_found != '':
            return True, tag_found, target_tag
        else:
            return False, None, target_tag

    def match_leq(major=None, minor=None):
        target_tag = format_tag(major)
        tag_found = look_for(target_tag)

        if tag_found != '':
            tags = tag_found.splitlines()
            tags.reverse()

            for tag in tags:
                if major is not None:
                    target = minor
                    query = tag.split('.')[1] if '.' in tag else None
                else:
                    target = major
                    query = tag.split('.')[0] if '.' in tag else tag
                    query = query[1:]

                if query is not None:
                    if int(query) <= int(target):
                        return True, tag, target_tag

        return False, None, target_tag

    # step 1: try to find a tag for the specific kernel and patch
    if patch is not None:
        found, tag, target = match_exact(major, minor, patch)
        if found:
            print('Found exact match for {0}'.format(target))
            return tag
        else:
            print('No matching patch for {0}'.format(target))

    # step 2: try to find a tag for the kernel maj, min, and rc
    if rc is not None:
        found, tag, target = match_exact(major, minor, rc=rc)
        if found:
            print('Found exact match {0} for {1}'.format(tag, target))
            return tag
        else:
            print('No matching rc for {0}'.format(target))

    # step 3: try to find a tag for the kernel maj and min version
    found, tag, target = match_exact(major, minor)
    if found:
        print('Found exact match {0} for {1}'.format(tag, target))
        return tag
    else:
        print('No matching minor version for {0}'.format(target))

    # step 4: try to build from closest tag less than minor version
    found, tag, target = match_leq(major, minor)
    if found:
        print('Using {0} as closest minor version for {1}'.format(tag, target))
        return tag
    else:
        print('No matching minor version for {0}'.format(target))

    # step 5: try to build from closest tag less than major version
    found, tag, target = match_leq(major)
    if found:
        print('Using {0} as closest major version for {1}'.format(tag, target))
        return tag
    else:
        print('No lower versions for {0}'.format(target))

    # step 6: try to build from the latest tag, if this fails the patches need updating
    rec_tag = run(['git', 'describe', '--abbrev=0'], stdout=PIPE).stdout.decode('utf-8').strip()
    print('Using latest tag on branch: {0}'.format(rec_tag))
    return rec_tag