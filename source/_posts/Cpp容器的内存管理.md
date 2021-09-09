---
title: Cpp容器的内存管理
abbrlink: 56ebe54a
date: 2021-09-09 15:11:12
categories: Operation System
tags: Memory Management
---

以C++中常用的vector、set为例，分析其数据在内存中的存储位置，并且探究容器内部内存释放的相关问题。

<!--more-->

# 1 容器相关变量在堆上还是在栈上

```c++
#include <string>
#include <set>
#include <vector>

using namespace std;

struct Node {
    vector<int> v;
};

int main() {
    vector<int> v1; // 栈区定义vector变量v1
    v1.push_back(1);
    printf("v1:             %p\n", &v1); // 变量v1的地址
    printf("v1 first ele:   %p\n", &(v1[0])); // 数组v1中第一个元素的存储地址

    set<int> s; // 栈区定义set变量s
    s.insert(1);
    printf("s:              %p\n", &s); // 变量s的地址
    printf("s first ele:    %p\n", s.begin()); // 集合s中第一个元素的存储地址

    vector<int> v2; // 栈区定义vector变量v2
    v2.push_back(1);
    printf("v2:             %p\n", &(v2)); // 变量v2的地址
    printf("v2 first ele:   %p\n", &(v2[0])); // 数组v2中第一个元素的存储地址

    /* ------------------------------------------------------------------- */

    Node n1; // 栈上定义结构体对象，其成员变量也在栈上
    n1.v.push_back(1);
    printf("n1:             %p\n", &(n1)); // 变量n1的地址
    printf("n1.v:           %p\n", &(n1.v)); // n1中的数组成员变量的存储地址
    printf("n1.v[0]:        %p\n", &(n1.v[0])); // n1中数组的首元素存储地址

    Node *n2 = new Node(); // 堆上定义结构体对象，这个变量在栈上，但它申请的内存在堆上
    n2->v.push_back(1);
    printf("n2:             %p\n", &(n2)); // 变量n2的地址
    printf("n2->v:          %p\n", &(n2->v)); // n2中的数组成员变量的存储地址
    printf("n2->v[0]:       %p\n", &(n2->v[0])); // n2中数组的首元素存储地址

    return 0;
}
```

编译后运行可得：

```
v1:             000000000062fdd0
v1 first ele:   0000000002652580
s:              000000000062fda0
s first ele:    00000000026525a0
v2:             000000000062fd80
v2 first ele:   00000000026525d0
n1:             000000000062fd60
n1.v:           000000000062fd60
n1.v[0]:        00000000026525f0
n2:             000000000062fd58
n2->v:          0000000002652610
n2->v[0]:       0000000002652630
```

观察可知：06开头的地址的值不断减少，02开头的的地址的值不断增加，由此可判断，06开头为栈上的地址(栈向下生长)，02开头的地址为堆上的地址。

1. 由v1、s、v2的地址可知，创建容器时，定义容器的变量本身存放在栈上；
2. 由v1的第一个元素、s的第一个元素、v2的第一个元素的地址可知，容器所存储的元素存放在堆上；
3. 由n1、n2的地址可知，创建结构体对象时，不管是将分配的内存放在栈空间还是堆空间(new开辟)，其结构体变量都存放在栈上；
4. 由n1和n1.v的地址可知，如果在栈上分配结构体内存的话，结构体的第一个成员的地址和定义结构体对象的变量的地址相等，且都在栈上；
5. 由n2和n2->v的地址可知，如果在堆上分配结构体内存的话，指针变量本身存放在栈上，但该对象的成员变量都存放在堆上；
6. 不管是在栈上还是堆上分配结构体对象的内存，其成员变量中如果有容器，那么容器中的数据都存放堆上。

总结：

1. vector、set容器中，其数据都动态存储在堆空间的内存上；
2. 在栈区定义容器变量，变量本身存储在栈区，但是容器所存储的数据在堆区；
3. 在堆空间定义的容器变量，成员变量本身存储在堆区，容器所存储的数据也在堆区。

# 2 容器释放内存

我们往往会在一个程序中向vector中压入多个元素，在使用完vector中的元素之后，只是会用clear去清理vector中的元素，但清空容器就等于释放了内存吗？

### 2.0 两个概念

- capacity的意思是容量，此方法返回的是该vector对象最多能容纳多少个元素；

- size的意思是大小，此方法是返回该vector对象当前有多少个元素。

### 2.1 实验一：clear()

代码：

```c++
#include <iostream>
#include <vector>
#include <windows.h>
#include <psapi.h>

#pragma comment(lib, "psapi.lib")

using namespace std;

void showMemoryInfo(void) {
    HANDLE handle = GetCurrentProcess();
    PROCESS_MEMORY_COUNTERS pmc;
    GetProcessMemoryInfo(handle, &pmc, sizeof(pmc));
    cout << "memory: " << pmc.WorkingSetSize / 1000 << "K" << endl
         << "peek memory: " << pmc.PeakWorkingSetSize / 1000 << "K" << endl
         << "virtual memory: " << pmc.PagefileUsage / 1000 << "K" << endl
         << "peek virtual memory: " << pmc.PeakPagefileUsage / 1000 << "K" << endl;
}

int main() {
    vector<double> v;
    for (int i = 0; i < 10000000; ++i) {
        double temp = i / 0.5;
        v.push_back(temp);
    }
    cout << "---not clear---" << endl;
    cout << "capacity: " << v.capacity() << endl;
    showMemoryInfo();
    v.clear();
    cout << endl << "---clear---" << endl;
    cout << "capacity: " << v.capacity() << endl;
    showMemoryInfo();
    return 0;
}
```

编译时加上`-lpsapi`选项。

结果：

```
---not clear---
capacity: 16777216
memory: 85667K
peek memory: 139751K
virtual memory: 136581K
peek virtual memory: 203853K

---clear---
capacity: 16777216
memory: 85667K
peek memory: 139751K
virtual memory: 136581K
peek virtual memory: 203853K
```

可以看到，clear()并没有真正释放内存。实际上，clear()只是将容器的size置为0，但没有改变capacity。

### 2.2 clear() + shrink_to_fit()

C++11有了一个全新的shrink_to_fit()方法，该方法与clear()搭配使用，将vector所占用大小缩小到合适的范围。

代码：

```c++
#include <iostream>
#include <vector>
#include <windows.h>
#include <psapi.h>

#pragma comment(lib, "psapi.lib")

using namespace std;

void showMemoryInfo(void) {
    HANDLE handle = GetCurrentProcess();
    PROCESS_MEMORY_COUNTERS pmc;
    GetProcessMemoryInfo(handle, &pmc, sizeof(pmc));
    cout << "memory: " << pmc.WorkingSetSize / 1000 << "K" << endl
         << "peek memory: " << pmc.PeakWorkingSetSize / 1000 << "K" << endl
         << "virtual memory: " << pmc.PagefileUsage / 1000 << "K" << endl
         << "peek virtual memory: " << pmc.PeakPagefileUsage / 1000 << "K" << endl;
}

int main() {
    vector<double> v;
    for (int i = 0; i < 10000000; ++i) {
        double temp = i / 0.5;
        v.push_back(temp);
    }
    cout << "---not shrink---" << endl;
    cout << "capacity: " << v.capacity() << endl;
    showMemoryInfo();
    v.clear();
    v.shrink_to_fit();
    cout << endl << "---shrink---" << endl;
    cout << "capacity: " << v.capacity() << endl;
    showMemoryInfo();
    return 0;
}
```

编译时加上`-lpsapi`选项。

结果：

```
---not clear---
capacity: 16777216
memory: 85651K
peek memory: 139759K
virtual memory: 136581K
peek virtual memory: 203878K

---clear---
capacity: 0
memory: 5615K
peek memory: 139759K
virtual memory: 2093K
peek virtual memory: 203878K
```

可以看到，使用shrink_to_fit方法搭配clear方法可以快速释放掉vector所占用的内存，且capacity也变为0。

### 2.3 swap()

swap交换技巧实现内存释放思想：vector()使用vector的默认构造函数建立临时vector对象，再在该临时对象上调用swap成员函数。用swap(v)把原来的vector拷贝至一个全新的临时vector，然后原有的vector就会被自然销毁。

代码：

```c++
#include <iostream>
#include <vector>
#include <windows.h>
#include <psapi.h>

#pragma comment(lib, "psapi.lib")

using namespace std;

void showMemoryInfo(void) {
    HANDLE handle = GetCurrentProcess();
    PROCESS_MEMORY_COUNTERS pmc;
    GetProcessMemoryInfo(handle, &pmc, sizeof(pmc));
    cout << "memory: " << pmc.WorkingSetSize / 1000 << "K" << endl
         << "peek memory: " << pmc.PeakWorkingSetSize / 1000 << "K" << endl
         << "virtual memory: " << pmc.PagefileUsage / 1000 << "K" << endl
         << "peek virtual memory: " << pmc.PeakPagefileUsage / 1000 << "K" << endl;
}

int main() {
    vector<double> v;
    for (int i = 0; i < 10000000; ++i) {
        double temp = i / 0.5;
        v.push_back(temp);
    }
    cout << "---not swap---" << endl;
    cout << "capacity: " << v.capacity() << endl;
    showMemoryInfo();
    vector<double>().swap(v);
    cout << endl << "---swap---" << endl;
    cout << "capacity: " << v.capacity() << endl;
    showMemoryInfo();
    return 0;
}
```

编译时加上`-lpsapi`选项。

结果：

```
---not swap---
capacity: 16777216
memory: 85610K
peek memory: 139751K
virtual memory: 136581K
peek virtual memory: 203845K

---swap---
capacity: 0
memory: 5607K
peek memory: 139751K
virtual memory: 2093K
peek virtual memory: 203845K
```

可以看到，使用swap方法搭配也可以快速释放掉vector所占用的内存，且capacity也变为0。

总结：

1. clear()并没有释放内存，仅仅改变了size；
2. 真正释放内存要使用clear() + shrink_to_fit()，或者swap()。
