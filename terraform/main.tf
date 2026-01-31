provider "aws" {
  profile = "default"
  region  = "us-east-1"
}

resource "aws_dynamodb_table" "dynamodb" {
  name         = "dynamodb"
  hash_key     = "PK"
  range_key    = "SK"
  billing_mode = "PAY_PER_REQUEST"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }
}