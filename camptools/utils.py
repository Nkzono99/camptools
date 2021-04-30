import subprocess


def call(cmd, encoding='utf-8'):
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o_data, e_data = p.communicate()
    return o_data.decode(encoding), e_data.decode(encoding)
