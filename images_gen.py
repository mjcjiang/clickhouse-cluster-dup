import subprocess

if __name__ == "__main__":
    file_content = ""
    with open("./Dockerfile_temp") as file:
        file_content = file.read()
        
    for i in range(4):
        #生成特定Dockerfile文件
        index_str = "0" + str(i+1)
        temp_content = file_content.replace("{num}", index_str)
        with open("./Dockerfile", "w") as file:
            file.write(temp_content)

        #Docker build出image
        subprocess.run(["docker", "build", "-t", "redmagic039/clickhouse" + index_str, "."])
        #Push to docker hub
        subprocess.run(["docker", "image", "push", "redmagic039/clickhouse" + index_str])
        #Remove Dockerfile
        subprocess.run(["rm", "./Dockerfile"])
