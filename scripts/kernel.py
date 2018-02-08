import json
import uuid
from subprocess import check_call

kern_urls = {
    'mainline': 'git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git',
    'stable': 'git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git'
}


def get_table(name):
    return globals()[name]


class JsonTable:
    def __init__(self, key=None):
        self.key = key if key is not None else str(uuid.uuid4())

    def save(self):
        self.__class__.series[self.key] = self
        data = {k: d.__dict__ for k, d in self.__class__.series.items()}

        for d in data.values():
            for k, v in d.items():
                if issubclass(type(v), JsonTable):
                    d[k] = {'$key': v.key, '$table': v.__class__.__name__}

        with open(self.__class__.backing, 'w') as f:
            json.dump(data, f, indent=4)

    @classmethod
    def get(cls, key):
        return cls.series[key]

    @classmethod
    def load(cls):
        with open(cls.backing) as f:
            data = json.load(f)

        for d in data.values():
            for k, v in d.items():
                if isinstance(v, dict) and '$key' in v and '$table' in v:
                    fk_class = get_table(v['$table'])
                    val = fk_class.series[v['$key']]
                    d[k] = val

        cls.series = {k: cls(**d) for k, d in data.items()}


class KernelVersion(JsonTable):
    backing = 'db/kernel_version.json'

    def __init__(self, major=None, minor=None, patch=None, rc=None, key=None):
        super().__init__(key)

        self.major = major
        self.minor = minor
        self.patch = patch
        self.rc = rc

    def __str__(self):
        kstring = '{major}'

        if self.minor is not None:
            kstring += '.{minor}'

        if self.patch is not None:
            kstring += '.{patch}'

        if self.rc is not None:
            kstring += '-rc{rc}'

        return kstring.format(**self.__dict__)

    @classmethod
    def parse(cls, kernel_string):
        kspec = KernelVersion()

        if kernel_string.count(':') > 0:
            kversion, ktype = map(str.strip, kernel_string.split(':'))
        else:
            ktype = None
            kversion = kernel_string

        kversion_parts = kversion.split('.')
        kspec.major = int(kversion_parts[0])
        kminorpart = kversion_parts[1]

        if len(kversion_parts) > 2:
            kspec.minor = int(kminorpart)
            kpatch = kversion_parts[2]

            if '-' in kpatch:
                _, kspec.rc = map(lambda s: int(s.replace('rc', '')), kpatch.split('-'))
            else:
                kspec.patch = int(kpatch)

        else:
            if '-' in kminorpart:
                kspec.minor, kspec.rc = map(lambda s: int(s.replace('rc', '')), kminorpart.split('-'))
            else:
                kspec.minor = int(kminorpart)

        try:
            kspec = KernelVersion.match(kspec)
        except IndexError:
            pass
        finally:
            return kspec, ktype

    @classmethod
    def match(cls, version):
        return [kv for kv in KernelVersion.series.values() if ((kv.major == version.major) and
                                                               (kv.minor == version.minor) and
                                                               (kv.patch == version.patch) and
                                                               (kv.rc == version.rc))][0]


class KernelSeries(JsonTable):
    backing = 'db/kernel_series.json'

    def __init__(self, series_number=None, series_number_collapsed=None, key=None):
        super().__init__(key)

        self.series_number = series_number
        self.series_number_collapsed = series_number_collapsed

    @classmethod
    def from_version(cls, version):
        series_number = KernelVersion(major=version.major, minor=version.minor)

        try:
            series_number = KernelVersion.match(series_number)
        except IndexError:
            series_number.save()

        series_number_collapsed = '{v.major}{v.minor}'.format(v=series_number)
        series = KernelSeries(series_number=series_number, series_number_collapsed=series_number_collapsed)

        try:
            series = [s for s in KernelSeries.series if s.series_number.key == series.series_number.key][0]
        except IndexError:
            pass
        finally:
            return series


class Workspace(JsonTable):
    backing = 'db/workspace.json'

    def __init__(self, path, version, key):
        super().__init__(key)

        self.path = path
        self.version = version


class BuiltKernel(JsonTable):
    backing = 'db/built_kernel.json'

    def __init__(self, type, build_job_id, version, kernel_series, workspace, key):
        super().__init__(key)

        self.type = type
        self.build_job_id = build_job_id
        self.version = version
        self.kernel_series = kernel_series
        self.workspace = workspace


KernelVersion.load()
KernelSeries.load()
Workspace.load()
BuiltKernel.load()


def download_kernel_source(type):
    check_call(['git', 'clone', kern_urls[type], 'linux'])


def workspace_for(k):
    matches = [w for w in Workspace.series.values() if (
        (w.version.major <= k.major) and
        (w.version.minor <= k.minor) and
        (w.patch <= k.patch) and
        (w.rc <= k.rc)
    )]

    matches.sort(key=lambda w: (w.version.major, w.version.minor, w.version.patch, w.version.rc), reverse=True)

    try:
        return matches[0]
    except IndexError:
        return None


def built_kernels_dict():
    all_series = []

    series = KernelSeries.series.items()
    for s in series:
        bk = [b for b in BuiltKernel.series.items() if b.kernel_series == s]
        sd = s.__dict__
        sd['kernels'] = [b.__dict__ for b in bk]

        sd['series_number'] = str(s.series_number)
        del sd['key']

        for b, bb in zip(sd['kernels'], bk):
            del b['key']
            del b['series']
            b['version'] = str(bb.version)
            b['link_version'] = b['version']

            if bb.version.patch is None:
                bb.version.patch = 0
                b['link_version'] = str(bb.version)

            b['workspace'] = b['workspace']['path']

        all_series.append(sd)

    return {'series': all_series}
