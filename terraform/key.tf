resource "aws_key_pair" "deployer" {
  key_name   = "movie"
  public_key = file("C:/Users/Takashi Mizuno/.ssh/id_rsa.pub")
}