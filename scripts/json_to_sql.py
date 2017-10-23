import json

import kernel

with open('kernel.json') as f:
    data = json.load(f)

for s in data['series']:
    number, _ = kernel.KernelVersion.parse(s['series_number'])
    number.save()

    ks = kernel.KernelSeries.from_version(number)
    ks.save()

    for k in s['kernels']:
        kn, _ = kernel.KernelVersion.parse(k['kernel_number'])
        kn.save()

        b = kernel.BuiltKernel(version=kn, type=k['kernel_type'], build_job_id=k['build_job_id'], series=ks)
        b.save()
