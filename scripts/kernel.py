from peewee import *
from subprocess import check_call
from playhouse.shortcuts import model_to_dict

kern_urls = {
    'mainline': 'git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git',
    'stable': 'git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git'
}

db = SqliteDatabase('kernel.db')


class KernelVersion(Model):
    major = IntegerField()
    minor = IntegerField()
    patch = IntegerField(null=True)
    rc = IntegerField(null=True)

    def __str__(self):
        kstring = '{major}'

        if self.minor is not None:
            kstring += '.{minor}'

        if self.patch is not None:
            kstring += '.{patch}'

        if self.rc is not None:
            kstring += '-rc{rc}'

        return kstring.format(**self._data)

    @staticmethod
    def parse(kernel_string):
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
        except KernelVersion.DoesNotExist:
            pass
        finally:
            return kspec, ktype

    @staticmethod
    def match(version):
        return KernelVersion.select().where((KernelVersion.major == version.major) &
                                            (KernelVersion.minor == version.minor) &
                                            (KernelVersion.patch == version.patch) &
                                            (KernelVersion.rc == version.rc)).get()

    class Meta:
        database = db


class KernelSeries(Model):
    series_number = ForeignKeyField(KernelVersion)
    series_number_collapsed = CharField()

    @staticmethod
    def from_version(version):
        series_number = KernelVersion(major=version.major, minor=version.minor)

        try:
            series_number = KernelVersion.match(series_number)
        except KernelVersion.DoesNotExist:
            series_number.save()

        series_number_collapsed = '{v.major}{v.minor}'.format(v=series_number)
        series = KernelSeries(series_number=series_number, series_number_collapsed=series_number_collapsed)

        try:
            series = KernelSeries.select().where(KernelSeries.series_number == series.series_number).get()
        except KernelSeries.DoesNotExist:
            pass
        finally:
            return series

    class Meta:
        database = db


class BuiltKernel(Model):
    version = ForeignKeyField(KernelVersion)
    type = CharField()
    build_job_id = CharField(unique=True)
    series = ForeignKeyField(KernelSeries, related_name='kernels')

    class Meta:
        database = db


class Workspace(Model):
    version = ForeignKeyField(KernelVersion)
    path = CharField()

    class Meta:
        database = db


def download_kernel_source(type):
    check_call(['git', 'clone', kern_urls[type], 'linux'])


def workspace_for(k):
    condition = ((KernelVersion.major <= k.major) &
                 (KernelVersion.minor <= k.minor) &
                 ((KernelVersion.patch <= k.patch) | KernelVersion.patch.is_null() | (k.patch is None)) &
                 ((KernelVersion.rc <= k.rc) | KernelVersion.rc.is_null() | (k.rc is None)))

    query = (Workspace
             .select(Workspace).join(KernelVersion)
             .where(condition)
             .order_by(KernelVersion.major.desc(),
                       KernelVersion.minor.desc(),
                       KernelVersion.patch.desc(),
                       KernelVersion.rc.desc()))

    try:
        return query.get()
    except Workspace.DoesNotExist:
        return None


def built_kernels_dict():
    all_series = []

    series = KernelSeries.select()
    for s in series:
        bk = BuiltKernel.select().where(BuiltKernel.series == s)
        sd = model_to_dict(s)
        sd['kernels'] = [model_to_dict(b) for b in bk]

        sd['series_number'] = str(s.series_number)
        del sd['id']

        for b, bb in zip(sd['kernels'], bk):
            del b['id']
            del b['series']
            b['version'] = str(bb.version)

        all_series.append(sd)

    return {'series': all_series}

db.connect()
db.create_tables([KernelVersion, KernelSeries, BuiltKernel, Workspace], safe=True)
