# camptools
camphor用ツール

# インストール
```
  pip install camptools --user
```

# コマンド一覧
```
$ nmyqsub <job file> -m <message> -d <directory>
  jobを投入し、job情報を記録する(job_status.sh, joblist.shなどに使用)
  directoryを指定した場合、指定ディレクトリに移動後にqsubを実行

$ myqsub <job file> -m <message> -d <directory>
  jobを投入し、job情報を記録する(job_status.sh, joblist.shなどに使用)
  directoryを指定した場合、指定ディレクトリに移動後にqsubを実行
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

$ extentsim <from-dir> <to-dir> --run
  EMSESの継続シミュレーションを行う
  from-dirに存在するmpiemses3D, job.sh, SNAPSHOT1, generate_xdmf.pyをto-dirにコピーする
  runフラグを指定するとmyqsubによるジョブの投入まで行う

$ mymkdir --key <key> <directory>
  keyで指定した構成のディレクトリを作成する
  ディレクトリ構成の設定は~/copylist.jsonに記載する

$ cmdjob [-h] {register,create} ...
$ cmdjob register -ug <usergroup> -s <system> --local
  作成するjobの設定を登録する
  localフラグを指定するとそのディレクトリ以下での設定が変更される
$ cmdjob create <command> -o <output>
  commandを実行するジョブファイルを作成する
  出力ファイル名はoutputで指定(デフォルト: tmpjob.sh)

$ checkpoint {register, clear, list}
$ checkpoint register -m <message>
  カレントディレクトリをチェックポイントとして保存する
$ checkpoint clear -a -i <index>
  チェックポイントを削除する
  -aフラグを指定するとすべてのチェックポイントを削除する
  -iフラグを指定すると指定した番号をチェックポイントを削除する
$ checkpoint list
  チェックポイントのリストを表示する

  
```

