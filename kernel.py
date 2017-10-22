from peewee import *
from subprocess import check_call

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
            kspec.patch = int(kversion_parts[2])

        if '-' in kminorpart:
            kspec.minor, kspec.rc = map(lambda s: int(s.replace('rc','')), kminorpart.split('-'))
        else:
            kspec.minor = int(kminorpart)

        return kspec, ktype

    class Meta:
        database = db


class KernelSeries(Model):
    series_number = KernelVersion()
    series_number_collapsed = CharField()

    class Meta:
        database = db


class BuiltKernel(Model):
    version = ForeignKeyField(KernelVersion)
    type = CharField()
    build_job_id = CharField()
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


db.connect()
db.create_tables([KernelVersion, KernelSeries, BuiltKernel, Workspace], safe=True)
