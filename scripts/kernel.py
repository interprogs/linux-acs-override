import json
import uuid
import os
import glob
from subprocess import check_call

kern_urls = {
    'mainline': 'git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git',
    'stable': 'git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git'
}


def get_table(name):
    return globals()[name]


class JsonTable:
    def __init__(self, key=None, monolithic=True):
        self.key = key if key is not None else str(uuid.uuid4())
        self.monolithic = monolithic

    def save(self):
        self.__class__.series[self.key] = self
        data = {k: d.__dict__ for k, d in self.__class__.series.items()}

        for d in data.values():
            for k, v in d.items():
                if issubclass(type(v), JsonTable):
                    d[k] = {'$key': v.key, '$table': v.__class__.__name__}

        mono_data = {k: d for k, d in data.items() if d['monolithic']}
        nm_data = {k: d for k, d in data.items() if not d['monolithic']}

        for k, v in mono_data.items():
            del v['monolithic']

        for k, v in nm_data.items():
            del v['monolithic']

        if len(mono_data.keys()) > 0:
            with open(self.__class__.backing, 'w') as f:
                json.dump(mono_data, f, indent=4)

        if len(nm_data.keys()) > 0:
            backing_dir = '{}.d'.format(self.__class__.backing)
            print(backing_dir)
            os.makedirs(backing_dir, exist_ok=True)
            for k, v in nm_data.items():
                dpath = os.path.join(backing_dir, '{}.json'.format(k))
                with open(dpath, 'w') as f:
                    json.dump({k: v}, f, indent=4)

    @classmethod
    def get(cls, key):
        return cls.series[key]

    @classmethod
    def load(cls):
        with open(cls.backing) as f:
            data = json.load(f)

        backing_dir = '{}.d'.format(cls.backing)
        if os.path.exists(backing_dir) and os.path.isdir(backing_dir):
            for fn in glob.glob(os.path.join(backing_dir, '*.json')):
                with open(fn) as f:
                    d = json.load(f)

                    key = list(d.keys())[0]
                    value = d[key]

                    value['monolithic'] = False

                    data[key] = value

        for d in data.values():
            for k, v in d.items():
                if isinstance(v, dict) and '$key' in v and '$table' in v:
                    fk_class = get_table(v['$table'])
                    val = fk_class.series[v['$key']]
                    d[k] = val

        cls.series = {k: cls(**d) for k, d in data.items()}


class KernelVersion(JsonTable):
    backing = 'db/kernel_version.json'

    def __init__(self, major=None, minor=None, patch=None, rc=None, key=None, monolithic=True):
        super().__init__(key, monolithic)

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

    def __init__(self, series_number=None, series_number_collapsed=None, key=None, monolithic=True):
        super().__init__(key, monolithic)

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
        series_obj = KernelSeries(series_number=series_number, series_number_collapsed=series_number_collapsed)

        try:
            series_obj = [s for s in KernelSeries.series.values() if s.series_number.key == series_obj.series_number.key][0]
        except IndexError:
            pass
        finally:
            return series_obj


class Workspace(JsonTable):
    backing = 'db/workspace.json'

    def __init__(self, path, version, key=None, monolithic=True):
        super().__init__(key, monolithic)

        self.path = path
        self.version = version


class BuiltKernel(JsonTable):
    backing = 'db/built_kernel.json'

    def __init__(self, type, build_job_id, version, kernel_series, workspace, key=None, monolithic=True):
        super().__init__(key, monolithic)

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
    matches = [w for w in Workspace.series.values() if ((w.version.major <= k.major) and (w.version.minor <= k.minor))]
    matches.sort(key=lambda w: (w.version.major, w.version.minor, w.version.patch, w.version.rc), reverse=True)

    try:
        return matches[0]
    except IndexError:
        return None


def db_to_dict():
    all_series = []

    series = KernelSeries.series.values()
    for s in series:
        built_kernels = [b for b in BuiltKernel.series.values() if b.kernel_series == s]
        series_dict = s.__dict__

        series_dict['series_number'] = str(s.series_number)
        del series_dict['key']
        del series_dict['monolithic']

        series_dict['kernels'] = []

        for b in built_kernels:
            built_kernel_dict = {**b.__dict__}
            del built_kernel_dict['key']
            del built_kernel_dict['monolithic']
            del built_kernel_dict['kernel_series']

            built_kernel_dict['version'] = str(b.version)
            built_kernel_dict['link_version'] = built_kernel_dict['version']

            if b.version.patch is None:
                b.version.patch = 0
                built_kernel_dict['link_version'] = str(b.version)

            built_kernel_dict['workspace'] = b.workspace.path
            series_dict['kernels'].append(built_kernel_dict)

        all_series.append(series_dict)

    return {'series': all_series}


def dict_to_db(dict):
    for s in dict['series']:
        series_version, _ = KernelVersion.parse(s['series_number'])
        series = KernelSeries.from_version(series_version)
        series.save()

        for k in s['kernels']:
            workspace_path = k['workspace']
            workspace_matches = [w for w in Workspace.series.values() if w.path == workspace_path]

            if len(workspace_matches) == 0:
                workspace_version_string = workspace_path.split('/')[-1].strip()
                workspace_version, _ = KernelVersion.parse(workspace_version_string)
                workspace_version.save()

                workspace = Workspace(workspace_path, workspace_version)
                workspace.save()
            else:
                workspace = workspace_matches[0]

            built_kernel_version_string = k['version']
            built_kernel_version, _ = KernelVersion.parse(built_kernel_version_string)
            built_kernel_version.save()

            built_kernel = BuiltKernel(k['type'], k['build_job_id'], built_kernel_version, series, workspace)
            built_kernel.save()
