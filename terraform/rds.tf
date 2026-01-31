# 変数（terraform apply 時に渡す）
variable "DB_NAME" {
  type = string
}

variable "USER_NAME" {
  type = string
}

variable "PASSWORD" {
  type      = string
  sensitive = true
}

# RDS 用セキュリティグループ（PostgreSQL 5432）
resource "aws_security_group" "rds_sg" {
  vpc_id = aws_vpc.main.id
  name   = "rds_security_group"

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# RDS は複数サブネットに配置できる必要があるため subnet group を作る
resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "rds_subnet_group"
  subnet_ids = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]
}

resource "aws_db_instance" "rds" {
  allocated_storage = 20
  engine            = "postgres"
  instance_class    = "db.t3.micro"

  db_name  = var.DB_NAME
  username = var.USER_NAME
  password = var.PASSWORD

  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  publicly_accessible = true
  skip_final_snapshot = true
}

output "db_instance_endpoint" {
  value = aws_db_instance.rds.endpoint
}