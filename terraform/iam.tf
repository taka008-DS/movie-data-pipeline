# 1. EC2が「自分を使っていいよ」とAWSにお願いするためのロール
resource "aws_iam_role" "ec2_role" {
  name = "ec2_data_pipeline_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# 2. ロールに「管理者権限（または特定権限）」を付与する
# 今回は学習用として強めの権限（AdministratorAccess）を付けていますが、本来は必要な分だけに絞ります
resource "aws_iam_role_policy_attachment" "role_attach" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

# 3. ロールをEC2にセットするための「プロフィール」という箱
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "ec2_data_pipeline_profile"
  role = aws_iam_role.ec2_role.name
}