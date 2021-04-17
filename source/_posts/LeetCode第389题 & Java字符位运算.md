---
title: LeetCode第389题 & Java字符位运算
abbrlink: 7b768b28
date: 2021-04-17 12:15:46
categories:
tags:
---

# 1 背景

[LeetCode第389题-找不同](https://leetcode-cn.com/problems/find-the-difference/)：

给定两个字符串 s 和 t，它们只包含小写字母。
字符串 t 由字符串 s 随机重排，然后在随机位置添加一个字母。
请找出在 t 中被添加的字母。

<!--more-->

示例 1：

```
输入：s = "abcd", t = "abcde"
输出："e"
解释：'e' 是那个被添加的字母。
```

示例 2：

```
输入：s = "", t = "y"
输出："y"
```

示例 3：

```
输入：s = "a", t = "aa"
输出："a"
```

示例 4：

```
输入：s = "ae", t = "aea"
输出："a"
```

提示：

- 0 <= s.length <= 1000
- t.length == s.length + 1
- s 和 t 只包含小写字母

解法之一可以将字符串s和字符串t拼接起来，之后对拼接后的字符串的每个字符进行**异或**运算，从而找到多余的那个字符。此处的异或运算的技巧应用可见[LeetCode第136题-只出现一次的数字](https://leetcode-cn.com/problems/single-number/)。

# 2 字符串拼接

将两个字符串拼接最简单的方法就是用```+```符号，但是效率很低，因为Java中对String对象进行```+```的操作实际上是一个不断创建新的对象并且将旧的对象回收的一个过程，所以执行速度很慢。

因此，可考虑用**StringBuilder**和**StringBuffer**两个类进行字符串拼接的操作，用法如下：

```
StringBuffer stringBuffer = new StringBuffer().append("abcd").append("abcde");
```

```
StringBuilder stringBuilder = new StringBuilder().append("abcd").append("abcde");
```

先有StringBuffer后有StringBuilder，两者就像是孪生双胞胎，该有的都有，只不过大哥 StringBuffer因为多呼吸两口新鲜空气，是**线程安全**的。

使用+号进行拼接字符串时，会创建了多个StringBuilder对象，而使用StringBuffer或StringBuilder的话，至始至终只有一个对象。

# 3 字符位运算

## 3.1 错误解法

回归这道题，根据位运算解法，一开始我的思路是：初始化一个char类型的数据为**空格**，之后遍历拼接后的字符串中的每个字符，不断进行位运算，遍历结束后得到的就是答案。后来发现本来应该输出小写的e，结果输出了大写的E。自己测试的代码如下：

```
public static void main(String[] args) {
    StringBuffer stringBuffer = new StringBuffer().append("abcd").append("abcde");

    char res = ' ';

    for (int i = 0; i < stringBuffer.length(); i++) {
        res ^= stringBuffer.charAt(i);
    }

    System.out.println(res); // E
}
```

分析：当res一直异或到abcdabcd时，由于abcdabcd相互异或的结果为0，因此此时的res为空格，ASCII码为32（0010 0000）。而空格和小写e异或的结果为：0010 0000 ^ 0110 0101 = 0100 0101，这个值为大写E的ASCII码。因此，如果res初始时为空格，一直进行异或操作的话会得到错误结果。如果想要得到正确的结果，那么res应该初始化为**NULL（ASCII码为0000 0000）**，而任意数和0异或的结果都等于这个数本身，这样子才不会影响异或运算的结果。

## 3.2 正确解法

然而，Java的基本类型char没有办法初始化为NULL，因此，不能用这种方法进行初始化和异或运算，而应该用每个字符的**ASCII码**进行异或运算，这样res初始化时就可以用0表示空。

```
public static void main(String[] args) {
    StringBuffer stringBuffer = new StringBuffer().append("abcd").append("abcde");

    int res = 0;

    for (int i = 0; i < stringBuffer.length(); i++) {
        res ^= (int) stringBuffer.charAt(i);
    }

    System.out.println((char) res); // e
}
```

# 4 总结

1. Java中的字符串拼接应该使用StringBuffer和StringBuilder两个类的append方法，效率高。而StringBuffer适用于多线程下的操作；
2. char类型的空字符会“污染”字符之间的异或运算结果，应该用int类型并初始化为0，表示NULL的ASCII码，然后在int类型上进行异或运算。