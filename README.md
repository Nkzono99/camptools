# camptools
camphor用ツール

## インストール
```
  pip install camptools
```

## コマンド一覧
### ジョブを投入し、ジョブIDを記録する
```
$ nmysbatch <job file> -m <message> -d <directory>
  jobを投入し、job情報を記録する(job_status.sh, joblist.shなどに使用)
  directoryを指定した場合、指定ディレクトリに移動後にqsubを実行

$ mysbatch <job file> -m <message> -d <directory>
  jobを投入し、job情報を記録する(job_status.sh, joblist.shなどに使用)
  directoryを指定した場合、指定ディレクトリに移動後にqsubを実行
  投入されるjobファイルは、パラメータファイルplasma.inpに応じてノード数を決定し置換したもの
  python環境にf90nmlが必要
  
  <job file>の形式は以下のようにすること
    1. #SBATCH --rsc p=32:t=1:c=1
```

### 実行中のジョブ状態を確認する
```
$ job_status
  jobの状態と標準出力の一部を出力

$ joblist
  jobの状態を出力
```

### これまでに投入したジョブ一覧を表示する
```
$ jobhistory -n <num outputs> --correct_date
  過去のjobのリストを表示
  <job id>, <directory>, <message>, <date>

  --correct_date: 
    *.o*ファイルから日付を読み取りjobに日付情報を付加する
    (この日付情報は保存されるため毎回呼ばなくても良い)
```

### EMSESの継続ジョブを投入する
```
$ extentsim <from-dir> <to-dir> --run
  EMSESの継続シミュレーションを行う
  from-dirに存在するmpiemses3D, job.sh, SNAPSHOT1, generate_xdmf.pyをto-dirにコピーする
  runフラグを指定するとmyqsubによるジョブの投入まで行う
```

### ディレクトリセットを作成する
```
$ mymkdir --key <key> <directory>
  keyで指定した構成のディレクトリを作成する
  ディレクトリ構成の設定は~/copylist.jsonに記載する
```

```copylist.json```
```
{
  "main": [
        "/home/**/*****/large0/Github/MPIEMSES3D/bin/mpiemses3D",
        "/home/**/*****/large0/job.sh",
        "/home/**/*****/large0/plot_example.ipynb"
  ],

  "emses": [
        "/home/**/*****/large0/Github/MPIEMSES3D/bin/mpiemses3D",
  ],
}
```

### 簡易的なジョブファイルを作成する
```
$ cmdjob [-h] {register,create} ...
$ cmdjob register -ug <usergroup> -s <system> --local
  作成するjobの設定を登録する
  localフラグを指定するとそのディレクトリ以下での設定が変更される
$ cmdjob create <command> -o <output>
  commandを実行するジョブファイルを作成する
  出力ファイル名はoutputで指定(デフォルト: tmpjob.sh)
```

### よく使うディレクトリのパスを記録する
```
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

### システム内で同期をとる
```
$ filesync {lock, wait, notify}
$ filesync lock <key>
  <key>名のロックを確保する (~/.camptools内にロック情報を書き込む)
$ filesync wait <key>
  <key>名のロックが確保されていたら待機する
$ filesync notify <key>
  <key>名のロックを解放する (~/.camptoolsからロック情報を削除する)
```

### preinp

`preinp` は、Fortran の `NAMELIST` 入力ファイル用プレプロセッサを Python で実装した軽量ツールです。
マクロを用いた定義・演算により、手作業では煩雑になりがちなパラメータ生成を自動化できます。

#### オプション一覧

| オプション                 | 説明             | デフォルト           |
| --------------------- | -------------- | --------------- |
| `-d`, `--directory`   | 入力ファイル所在ディレクトリ | `./`            |
| `-i`, `--preinp_file` | 前処理対象ファイル名     | `plasma.preinp` |
| `-o`, `--output`      | 出力ファイル名        | `plasma.inp`    |
| `-v`, `--verbose`     | 詳細ログを表示        | オフ              |

#### 実行例

```bash
# 入力ディレクトリ './input' の 'plasma.preinp' を処理
preinp -d input -i plasma.preinp -o plasma.inp

# 詳細ログ付き
preinp -v
```

#### マクロ記法

* `!!>` で始まる行をマクロ処理の対象とし、末尾に `\` を付けると行継続できます。
* **一時変数の定義**: `var symbol = value` で計算中に利用する変数を登録。
* **定数定義**: `symbol = value` または `symbol(index) = val1, val2` で、最終的に出力される NAMELIST 値を指定。
* **算術演算・条件式**: `+`, `-`, `*`, `/`, `min(a,b)`, `x if cond else y` など。
* **単位変換**: （オプション）`unit.<name>.trans(value)` / `unit.<name>.reverse(value)` を利用可能。

#### Example

`plasma.preinp`:

```fortran
!!key dx=[0.001],to_c=[10000.0]
&simulation
!!> var nx = 128
!!> var ny = 64
!!> total_cells = nx * ny
!!> velocity = unit.v.trans(10000)
/
```

生成される `plasma.inp`:

```fortran
&simulation
    total_cells = 8192
    velocity = 0.33356409519815206
/
```

#### 単位変換についての補足

- ```物理単位系 → EMSES単位系```変換 (```unit.<name>.trans(value)```)
- ```EMSES単位系 → 物理単位系```変換 (```unit.<name>.reverse(value)```)

```<name>```　一覧

```
B = Magnetic flux density [T]
C = Capacitance [F]
E = Electric field [V/m]
F = Force [N]
G = Conductance [S]
J = Current density [A/m^2]
L = Inductance [H]
N = Flux [/m^2s]
P = Power [W]
T = Temperature [K]
W = Energy [J]
a = Acceleration [m/s^2]
c = Light Speed [m/s]
e = Napiers constant []
e0 = FS-Permttivity [F/m]
eps = Permittivity  [F/m]
f = Frequency [Hz]
i = Current [A]
kB = Boltzmann constant [J/K]
length = Sim-to-Real length ratio [m]
m = Mass [kg]
m0 = FS-Permeablity [N/A^2]
mu = Permiability [H/m]
n = Number density [/m^3]
phi = Potential [V]
pi = Circular constant []
q = Charge [C]
q_m = Charge-to-mass ratio [C/kg]
qe = Elementary charge [C]
qe_me = Electron charge-to-mass ratio [C/kg]
rho = Charge density [C/m^3]
t = Time [s]
v = Velocity [m/s]
w = Energy density [J/m^3]
```
