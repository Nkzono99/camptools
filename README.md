# camptools
camphor用ツール

## インストール

```bash
  pip install camptools
```

## コマンド一覧
### ジョブを投入し、ジョブIDを記録する

```bash
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

---

### 実行中のジョブ状態を確認する

```bash
$ job_status
  jobの状態と標準出力の一部を出力

$ joblist
  jobの状態を出力

$ latestjob
  現在のディレクトリで実行された直近のジョブの標準出力の一部を表示
```

---

### EMSESの継続ジョブを投入する

```bash
$ extentsim <from-dir> <to-dir> --run
  EMSESの継続シミュレーションを行う
  from-dirに存在するmpiemses3D, job.sh, SNAPSHOT1, generate_xdmf.pyをto-dirにコピーする
  runフラグを指定するとmysbatchによるジョブの投入まで行う
```

---

### ディレクトリセットを作成する

```bash
$ mymkdir --key <key> <directory>
  keyで指定した構成のディレクトリを作成する
  ディレクトリ構成の設定は~/copylist.jsonに記載する
```

<details>

<summary>copylist.json</summary>

```json
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

</details>

---

### シミュレーションバグレポート自動収集スクリプト

以下のコマンド出力をまとめて Markdown 形式のレポート (`report.md`) を自動生成.

1. カレントディレクトリ（`pwd`）  
2. MPIEMSES3D のバージョン情報（`module load hdf5 fftw; ./mpiemses3D --version`）  
3. 入力ファイル内容（`cat plasma.inp`）  
4. 最新ジョブのログ（`latestjob -n 100` / `latestjob -n 100 -e`）  

シミュレーションディレクトリで以下のように実行し、報告時に必要な最小限のデータを集約する。

```bash
$ collect_report

```

---

### これまでに投入したジョブ一覧を表示する

```bash
$ jobhistory -n <num outputs> --correct_date
  過去のjobのリストを表示
  <job id>, <directory>, <message>, <date>

  --correct_date: 
    *.o*ファイルから日付を読み取りjobに日付情報を付加する
    (この日付情報は保存されるため毎回呼ばなくても良い)
```

---

### preinp

`preinp` は、Fortran の `NAMELIST` 入力ファイル用プレプロセッサを Python で実装した軽量ツールです。
マクロを用いた定義・演算により、手作業では煩雑になりがちなパラメータ生成を自動化できます。

<details>

<summary>Usage</summary>

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
    nx = 128
!!> var ny = 64
!!> total_cells = nx * ny
!!> velocity = unit.v.trans(10000)
/
```

生成される `plasma.inp`:

```fortran
&simulation
    nx = 128
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

</details>

---

### param_sweep

*YAML 1 枚から複数の EMSES解析ディレクトリを自動生成し、必要ならそのままジョブ投入まで行うツール。*

<details>
  
<summary>Usage</summary>
  
#### 1. 基本ディレクトリ構成

```text
project/
├── sweep.yaml            # ← ① サーベイ定義
└── plasma.preinp.j2      # ← ② Jinja2 テンプレート
```

実験ごとに複数の `*.yaml` / `*.j2` を置いても OK です。

#### 2. `sweep.yaml` の書き方

```yaml
# schemaは未用意
# $schema: https://raw.githubusercontent.com/USER/param_sweep/main/schema/sweep.schema.json

# 例: scale × ratio の 2×2 + 2×1 = 6 ケース
cases:
  - scale: [0.5, 1.0]
    ratio: [0.3, 1.0]
    nstep: 200000
  - scale: [0.5, 1.0]
    ratio: [0.6]
    nstep: 500000
```

* **`params:`**  … リストは *直積展開*、スカラーは共通値。
* **`cases:`**   … 手書きで追加・上書き・除外。`_skip` / `_only` が使用可。

#### 3. テンプレート (`plasma.preinp.j2`)

```fortran
&tmgrid
    dt = {{ dt | default(0.004) }}
    nx = {{ nx }}
    ny = {{ ny }}
    nz = {{ nz }}
/
```

* `{{ var }}` が YAML/計算結果で置換。
* `default()` フィルタで未定義時のフォールバックを設定可能。

#### 4. CLI の基本操作

```bash
# dry-run: ディレクトリ名だけ表示
$ param_sweep sweep.yaml --dry-run
exp_scale0p5_ratio0p3
exp_scale0p5_ratio0p6
…

# ディレクトリ生成＆preinp 実行（ジョブ未投入）
$ param_sweep sweep.yaml --template plasma.preinp.j2

# 生成後に mysbatch で投入
$ param_sweep sweep.yaml --run

# YAML を編集せずに一時上書き
$ param_sweep sweep.yaml -s ratio=10 --dry-run
```

※ コマンドラインの指定は YAML の設定より常に優先されます。

※ ディレクトリは```mymkdir```のデフォルトで生成されます。シミュレーションに必要なファイル群はそちらで指定してください。

#### 5. ディレクトリ名のルール

```
exp_scale0p5_ratio1_density1e6  # 0.5→0p5, 1e6→1M, 0.02→20m
```

* キーはアルファベット順。
* 値は *工学表記* で短縮化（`naming.safe()` を参照）。

#### 6. 典型的ワークフロー

```bash
$ vim sweep.yaml                # 範囲を追加
$ param_sweep sweep.yaml --dry-run    # 名称確認
$ param_sweep sweep.yaml --run        # 実行開始
```

変数を増やすときは

1. YAML の `params:` に追加
2. テンプレートに `{{ var }}` を追加
   だけで OK。

</details>
