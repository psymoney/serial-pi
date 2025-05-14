# virtual serial environment setup
## author's system environment overview
1. main os: Windows11
2. virtual os: wsl2, ubuntu 24.04


## basic environment setup
### 1. install socat
```bash
sudo apt update
sudo apt install socat
```

### 2. create virtual port pair
```bash
socat -d -d PTY,raw,echo=0 PTY,raw,echo=0
```

once run the above command, you will get two pseudo-terminals:
```bash
2025/05/14 13:00:00 socat[1234] N PTY is /dev/pts/3
2025/05/14 13:00:00 socat[1234] N PTY is /dev/pts/4
2025/05/14 13:00:00 socat[1234] N starting data transfer loop with FDs [5,5] and [7,7]
```

to work this on background, append `&`
```bash
socat -d -d PTY,raw,echo=0 PTY,raw,echo=0 &
```

## automate fetching the created port name 
- executor of the virt serial setup must be isolated in different process. otherwise, executor's performance will be counted either.



