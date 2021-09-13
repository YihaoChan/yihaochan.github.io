---
title: Linux中多线程环境下fork后重复加锁会引发死锁
categories: Operation System
tags: Linux-fork-thread-lock
abbrlink: 381fa2ee
date: 2021-09-13 21:19:04
---

简单实验表明：在Linux操作系统的多线程执行环境下，调用fork()函数后的子进程如果对已经加锁的锁继续加锁，则会使操作系统引发死锁；而让子线程对已经加锁的锁继续加锁的话，则能够避免死锁。

<!--more-->

# 1 实验背景

1. 主线程创建子线程；
2. 在子线程中对互斥量mutex上锁(lock)，然后sleep(5)；
3. 在第一步中，需要sleep(1)，确保主线程不要太快创建好子进程，以至于子进程创建好的时候第2步还没上好锁；
4. 当前进程的主线程fork一个子进程，此时子进程继承了父进程的锁及其状态，即：子进程此时的mutex是已经上了锁了的；
5. 在子进程中对mutex进行lock。

# 2 子进程加锁

对实验背景进行代码实现：

```c
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <wait.h>

pthread_mutex_t mutex;

void *func_thread(void *arg) {
    printf("child thread gets the lock\n");
    pthread_mutex_lock(&mutex);
    sleep(5);
    pthread_mutex_unlock(&mutex);
}

void func_proc() {
    printf("child process wants the lock\n");
    pthread_mutex_lock(&mutex);
    printf("test\n");
    pthread_mutex_unlock(&mutex);
}

int main() {
    pthread_mutex_init(&mutex, NULL);
    pthread_t tid;

    pthread_create(&tid, NULL, func_thread, NULL);
    sleep(1); // 确保在fork成功之前，子线程已经获得锁

    int pid = fork();
    if (pid < 0) {
        pthread_join(tid, NULL);
        pthread_mutex_destroy(&mutex);
        return 1;
    } else if (pid == 0) {
        func_proc();
        exit(0);
    } else {
        wait(NULL);
    }

    pthread_join(tid, NULL);
    pthread_mutex_destroy(&mutex);

    printf("end\n");
    return 0;
}
```

运行后终端回显如下：

![](/images/Linux中多线程环境下fork后重复加锁会引发死锁/fork_lock.png)

可见，程序无法运行下去，根本没办法运行到test那一行，故操作系统引发死锁。

# 3 子线程加锁

将子进程改为子线程，让子线程去加锁：

```c
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <wait.h>

pthread_mutex_t mutex;

void *func1(void *arg) {
    printf("child thread1 gets the lock\n");
    pthread_mutex_lock(&mutex);
    sleep(5);
    pthread_mutex_unlock(&mutex);
}

void *func2(void *arg) {
    printf("child thread2 wants the lock\n");
    pthread_mutex_lock(&mutex);
    printf("child thread2 successfly gets the lock\n");
    pthread_mutex_unlock(&mutex);
}

int main() {
    pthread_mutex_init(&mutex, NULL);
    pthread_t tid1, tid2;

    pthread_create(&tid1, NULL, func1, NULL);
    sleep(1); // 确保在thread2运行之前，thread1已经获得锁

    pthread_create(&tid2, NULL, func2, NULL);

    pthread_join(tid1, NULL);
    pthread_join(tid2, NULL);

    pthread_mutex_destroy(&mutex);

    printf("end\n");
    return 0;
}
```

运行后终端回显如下：

![](/images/Linux中多线程环境下fork后重复加锁会引发死锁/thread_lock.png)

可见，程序顺利运行直至结束，没有引发死锁。

# 4 简要分析

## 4.1 子进程

fork()有一个特点：子进程只拥有一个执行线程，而这个执行线程就是**调用fork的那个线程**的完整复制，除了调用fork的那个线程外，其余线程它根本不知道、不认识，**父进程中其他的线程在子进程中都会消失**。此外，子进程自动继承了父进程中互斥锁的状态(原来加锁了的话，现在还是加锁的)。

如果这个时候，对于已经加锁了但还没释放的锁，子进程依旧想对这个锁上锁的话，那么，把互斥锁加锁的那个线程会等待子进程释放锁，子进程又会等待那个线程释放锁才能获得锁，故导致了死锁。并且，我们无法对该锁进行解锁，因为**在子进程中，该锁的持有者并不存在**，它根本不知道是哪个线程谁给这个互斥锁加了锁。

## 4.2 子线程

解决方法之一，是不要用子进程去加锁，而采用**子线程**。一般情况下两个线程对同一个mutex进行lock，并不会造成死锁，后lock的线程会**进入等待状态**，直到前一个线程进行unlock。

在Linux中，互斥锁的类型默认为PTHREAD_MUTEX_NORMAL，代表普通锁。当一个线程对一个普通锁加锁以后，其余请求对该锁加锁的线程将形成一个**等待队列**，并在该锁解锁后按优先级获得它。但是，这样会导致一个问题：一个线程如果对一个已经加锁的普通锁再次加锁，也就是这个线程对这个锁加两遍锁，那么就会引发死锁。试想一下：等待队列里面是自己这个线程本身，那么释放后的锁又给了自己，又被自己上了锁，那肯定就是死锁了。

```c
int res = (PTHREAD_MUTEX_NORMAL == PTHREAD_MUTEX_DEFAULT) ? 1 : 0;
printf("%d", res);
```

res为1，说明Linux默认的锁的类型就是上述这种普通锁。