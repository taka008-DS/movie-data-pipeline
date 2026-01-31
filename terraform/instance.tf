resource "aws_instance" "web" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = "t2.micro"
  subnet_id                   = aws_subnet.public_subnet_1.id
  associate_public_ip_address = true
  security_groups             = [aws_security_group.ec2_sg.id]
  key_name                    = aws_key_pair.deployer.key_name
  connection {
    type        = "ssh"
    user        = "ec2-user"
    private_key = file("/c/Users/Takashi Mizuno/.ssh/id_rsa")
    host        = self.public_ip
  }
}
output "instance_public_ip" {
  description = "The public IP address of the web instance"
  value       = aws_instance.web.public_ip
}
