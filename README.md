# このレポジトリについて
このレポジトリは[HCCJP](www.hccjp.org)の環境構築等に使用するコード類をまとめています。
主に下記の処理を行っています。

- Terraformを使用してAzure上にVMとWebAppsの作成
- Ansibleを使用してVMの構成
  - Azure Stack用の証明局の作成
- Azure Stack用の証明書の作成
- Azure Stack上への検証用ユーザーおよびサブスクリプションの作成
- 検証用Azure環境とのハイブリッドネットワークの構成(ExpressRoute接続)

# 簡単なハンズオンの実行方法(※研修用)
## Cloud Shellへのアクセス
1. Azure Portalへのログイン
1. Cloud Shellの実行(Bash)

## サブスクリプションの選択

```
az account list #サブスクリプション一覧の確認
az account set --subscription サブスリプション名 #利用するサブスクリプションの設定
az account show #確認
```

## ソースコードの取得

```
git clone https://github.com/ebibibi/hccjp.git
```

## Terraform用の設定

```
cd hccjp
cd Terraform
cp terraform.tfvars.sample terraform.tfvars
emacs terraform.tfvars #変数の定義(ファイル保存はCtrl-x, Ctrl-s。emacs終了はCtrl-x, Ctrl-c)
emacs WindowsVM.tf
rm Web.tf
rm ExpressRoute.tf
```

## Terraform実行

```
terraform init
terraform plan
terraform apply
```
