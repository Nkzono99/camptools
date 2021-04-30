# camptools
camphor用ツール

# インストール
```
  pip install git+https://github.com/Nkzono99/camptools.git
```

# コマンド一覧
```
$ nmyqsub <job file> -m <message>
  jobを投入し、job情報を記録する(job_status.sh, joblist.shなどに使用)

$ myqsub <job file> -m <message>
  jobを投入し、job情報を記録する(job_status.sh, joblist.shなどに使用)
  投入されるjobファイルは、パラメータファイルplasma.inpに応じてノード数を決定し置換したもの
  python環境にf90nmlが必要
  
  <job file>の形式は以下のようにすること
    1. #QSUB -A p={}:t=1:c=64:m=90G
    2. aprun -n {} -d 1 -N 64 ./mpiemses3D plasma.inp

$ job_status
  jobの状態と標準出力の一部を出力

$ joblist
  jobの状態を出力

$ jobhistory -n <num outputs> --correct_date
  過去のjobのリストを表示
  <job id>, <directory>, <message>, <date>

  --correct_date: 
    *.o*ファイルから日付を読み取りjobに日付情報を付加する
    (この日付情報は保存されるため毎回呼ばなくても良い)

```

