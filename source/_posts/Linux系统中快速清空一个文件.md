---
title: Linux系统中快速清空一个文件
categories: Operation System
tags: Linux-clear-file
abbrlink: d6d3eae9
date: 2021-09-14 17:00:17
---

需求：在Linux系统中，如何快速清空一个10G的文件？

<!--more-->

# 1 回答1：rm命令(错误)

执行rm命令并没有**真正删除**文件，而只是对这个文件做了`unlink`操作，删除对这个文件的链接。但在磁盘上，这个文件的数据和这些数据块仍然保留着，rm命令执行后，操作系统把inode和数据块都标记为`unused`，但并没有真正擦去这些数据，文件的内容会被下次写入的内容覆盖。

# 2 方法1：null重定向

将null重定向到文件中，可以快速清空文件的内容，或者说，使一个文件变为空白：

1. 执行`dd if=/dev/zero of=50M.file bs=1M count=50`创建一个50M的文件；
2. 备份50M.file为backup；
3. 执行`du -h backup`查看文件大小，为50M；
4. 执行`> backup`清空文件内容；
5. 再次执行`du -h backup`查看文件大小，为0。

![](/images/Linux系统中快速清空一个文件/null_redirect.png)

# 3 方法2：冒号重定向

Linux系统中，冒号`:`是一个内置符号，它什么也不做，充当一个no-op(无操作)。比如在编写脚本的过程中，某些语法结构需要多个部分组成，但开始阶段并没有想好或完成相应的代码，这时就可以用`:`来做占位符，否则执行时就会报错。

```bash
if [ "today" == "2021-09-14" ]; then 
    : 
else 
    : 
fi 
```

因此，可通过冒号重定向来快速清空文件内容：

1. 执行`dd if=/dev/zero of=50M.file bs=1M count=50`创建一个50M的文件；
2. 备份50M.file为backup；
3. 执行`du -h backup`查看文件大小，为50M；
4. 执行`: > backup`清空文件内容；
5. 再次执行`du -h backup`查看文件大小，为0。

![](/images/Linux系统中快速清空一个文件/colon_redirect.png)

# 4 方法3：truncate命令

truncate命令可被用来将一个文件缩小或者扩展到某个给定的大小，可以利用它和 -s 参数来特别指定文件的大小。要清空文件的内容，则在下面的命令中将文件的大小设定为0：

1. 执行`dd if=/dev/zero of=50M.file bs=1M count=50`创建一个50M的文件；
2. 备份50M.file为backup；
3. 执行`du -h backup`查看文件大小，为50M；
4. 执行` truncate -s 0 backup`清空文件内容；
5. 再次执行`du -h backup`查看文件大小，为0。

![](/images/Linux系统中快速清空一个文件/truncate.png)

# 5 方法4：rsync命令

假如你要在linux下删除大量文件，比如100万、1000万，像/var/spool/clientmqueue/的mail邮件，/usr/local/nginx/proxy_temp的nginx缓存等，那么rm -rf可能就会很慢。此时，可用rsync来清空目录或文件：

1. 准备一个52M的目录，命名为backup；

2. 执行`du -sh backup`查看目录大小，为52M；

3. 建立一个空目录：`mkdir empty`；

4. 用rsync删除目标目录：`rsync --delete-before -d ./empty ./backup`。参数说明：

   ```
   -delete-before：接收者在传输之前进行删除操作
   -d：传输的文件是目录
   ```

   相当于把空目录替换到该目录中；

5. 再次执行`du -h backup`查看文件大小，为0。

![](/images/Linux系统中快速清空一个文件/rsync.png)

为什么rsync能够快速删除大文件？

1. rm命令大量调用了lstat64和unlink，可以推测删除每个文件前都从文件系统中做过一次lstat操作。过程：正式删除工作的第一阶段，需要通过getdirentries64调用，分批读取目录(每次大约为4K)，在内存中建立rm的文件列表；第二阶段，lstat64确定所有文件的状态；第三阶段，通过unlink执行实际删除。这三个阶段都有比较多的系统调用和文件系统操作；
2. rsync所做的系统调用很少：没有针对单个文件做lstat和unlink操作。命令执行前期，rsync开启了一片共享内存，通过mmap方式加载目录信息。只做目录同步，不需要针对单个文件做unlink。另外，在其他人的评测里，rm的上下文切换比较多，会造成System CPU占用较多。 rm删除内容时，将目录的每一个条目逐个删除(unlink)，需要循环重复操作很多次；rsync删除内容时，建立好新的空目录，替换掉老目录，基本没开销。rsync命令**只对文件做unlink操作**，不做其他读取文件数据、检查应不应该被unlink等等操作，就是很**纯粹地unlink**。这就是`rsync`快的原因。

# 参考链接

1. https://unix.stackexchange.com/questions/10883/where-do-files-go-when-the-rm-command-is-issued
2. https://blog.csdn.net/sd4493091/article/details/80414053
3. https://www.quora.com/What-does-rsync-do-that-makes-it-so-efficient-at-deleting-many-small-files

