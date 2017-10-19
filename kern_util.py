from subprocess import check_call

kern_urls = {
    'mainline': 'git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git',
    'stable': 'git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git'
}


def kernel_spec(major=None, minor=None, patch=None, rc=None, type=None):
    args = locals()
    kspec = {k: args[k] for k in ['major', 'minor', 'patch', 'rc', 'type']}
    return kspec


def parse_kernel(kernel_string):
    kspec = kernel_spec()

    if kernel_string.count(':') > 0:
        kversion, kspec['type'] = map(str.strip, kernel_string.split(':'))
    else:
        kversion = kernel_string

    kversion_parts = kversion.split('.')
    kspec['major'] = kversion_parts[0]
    kspec['minor'] = kversion_parts[1]

    if len(kversion_parts) > 2:
        kspec['patch'] = kversion_parts[2]

    if '-' in kspec['minor']:
        kspec['minor'], kspec['rc'] = kspec['minor'].split('-')

    return kspec


def format_kernel(kspec):
    kstring = '{major}.{minor}'

    if kspec['patch'] is not None:
        kstring += '.{patch}'

    if kspec['rc'] is not None:
        kstring += '-{rc}'

    return kstring.format(**kspec)


def download_kernel_source(kspec):
    check_call(['git', 'clone', kern_urls[kspec['type']], 'linux'])
