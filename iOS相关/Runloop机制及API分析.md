[TOC]

# 引言

​	这块内容涉及到的知识点相当之多，建议读者在阅读本文时在Playground中多运行代码，加以实践，配合苹果官方的文档（强烈推荐）和网络上其他文章辅助理解。

# 什么是Runloop

​	Runloop是一种事件处理机制和对象，它可以监听整个Runloop对象内部所拥有的计时器（TImer）和事件源（Source），当这两者的事件触发（包括但不限于收到来自外部的输入，计时器到时）时，Runloop就会调用其相关的Thread来处理这些事件，可以实现对线程资源的持久利用。我们的主线程出生就自带有一个Runloop，用来处理应用生命周期中的各类事件，就像一个loop（循环）不停的run（运行）下去

# Runloop和线程

​	Runloop的存在依托于线程Thread，它利用Thread的计算资源来处理它所接收到的各类事务。一般情况下，以NSThread为例，NSThread在运行完自身的任务后就会退出；如果使用了Runloop，则NSThread会在Runloop退出之前一直存在，实现了NSThread的持久化，可以用于应对一众需要线程长时间存活的业务情况，经典的例子就是AFNetworking 2.x版本的实现；它利用Runloop实现了一条持久化线程，用以初始化网络请求，并且接受来自服务器的响应。

# Runloop的相关类实现

​	Runloop在swift中的实现有两个，Runloop和CFRunloop，前者是对后者的包装，而后者是CoreFoundation框架内的，提供纯C函数API的实现。本文以CFRunloop为示例API，感兴趣的读者请自行查阅Runloop API进行学习

​	所有CFRunLoop中的函数和类，都是以CFRunLoop开头的名字。在CFRunloop中，我们一般会接触到以下五种对象

+ CFRunLoop —— 对应一个Runloop对象

+ CFRunLoopMode ——Runloop模式，代表了Runloop中会出现的运行模式

+ CFRunLoopSource —— Runloop事件源，分为source0和source1两种，可以根据需要向Runloop发送事件信号以唤醒Runloop

+ CFRunLoopTimer —— Runloop计时器，顾名思义，可以在Runloop中定时发送信号唤醒Runloop

+ CFRunLoopObserver —— Runloop监视器，可以监视整个Runloop中一个或多个阶段的状态变化，并且能根据用户设定做出相应的操作

  接下来，文章会分类讲解这五个对象

## CFRunLoop

​	作为Runloop的一个核心类，CFRunLoop对象只能由工厂模式生产。想在一个自定义的子线程中获取到专属CFRunLoop对象，只需要在子线程的方法闭包中调用`CFRunLoopGetCurrent()`即可。在调用该方法之前，线程中不存在CFRunLoop对象，自然也就没有Runloop的说法。调用时系统会自动创建一个CFRunLoop对象，并且将该对象与当前子线程绑定，之后再调用`CFRunLoopGetCurrent()`只会获取到当前已有的CFRunLoop对象，有兴趣的读者可以执行以下代码看看结果。

```swift
    let runloop = CFRunLoopGetCurrent()
    print(runloop == CFRunLoopGetCurrent())
```

​	在获取到了CRRunLoop对象之后，我们就可以自行向其中添加各类事件源、计时器和监视器了。

## CFRunLoopMode

​	CFRunLoop中存在有几个自带的运行模式，分别是

+ **kCFRunLoopDefaultMode**：默认的模式，绝大多数时间里App都运行在这个模式下

+ **UITrackingRunLoopMode**：用来追踪用户与UI交互活动的模式，这里交互活动特指Scrollview和继承了Scrollview的组件的滑动事件

+ UIInitializationRunLoopMode：应用启动进行初始化时会用到的模式

+ GSEventReceiveRunLoopMode：用来接受来自系统内部事件的模式

+ **kCFRunLoopCommonModes**：不是一种真正的模式，而是以上模式中一种或多种模式的集合，CFRunLoop无法在这种模式下运行。

  在开发中我们经常用到的，也就只有1、2、5三种模式

​	每个CFRunLoop对象都拥有一个或多个运行模式，我们在向CFRunLoop添加各类事件源、计时器和监视器时都需要指定运行模式，本质上就是在向CFRunLoop对象中的各类模式添加。想知道当前Runloop具有什么样的运行模式，可以使用`CFRunLoopCopyAllModes(rl: CFRunLoop!)`获得到包含当前Runloop所有运行模式的数组，如果想要切换Runloop的运行模式，则必须先停止Runloop，再重新指定运行模式开始运行。

​	Runloop在启动时，必须指定其中一种运行模式，且指定的运行模式中必须存在有Source和Timer，否则整个Runloop会直接退出。

​	这里要重点讲一下**kCFRunLoopCommonModes**这个模式，我们暂且称之为普通模式。正如上面所讲，普通模式并不是一种具体的模式，而是一个或多个其它模式的集合。CFRunLoop无法运行在这种模式下，但是Source，Timer和Observer都可以添加到该模式下，相当于允许这些Item在多个模式中运行，当CFRunLoop的模式发生切换以后它们仍然可以继续运行。因为我们的应用时刻会在模式间切换（最常见的就是在kCFRunLoopDefaultMode和UITrackingRunLoopMode两种模式之间切换），如果你想让一个Item持续工作，那你就得将它添加到普通模式中。

## CFRunLoopSource

​	CFRunLoopSource的存在允许用户和系统在一定条件下，向Runloop发送事件信号，让RunLoop对其进行处理。

​	按照水果开发文档的划分，我们可以将CFRunLoopSource分为两类：

1. Version 0（Source 0）—— 非基于mach_port的事件源
2. Version 1（Source 1）—— 基于mach_port的事件源

​	先说一下这个mach_port是个什么东西。

​	在iOS和MacOS中，其操作底层核心为Darwin，它包括了诸如系统内核，驱动和shell等等的内容。

<img src="https://blog.ibireme.com/wp-content/uploads/2015/05/RunLoop_4.png" alt="img" style="zoom:50%;" />

​	上图给出了Darwin核心的内部结构。其中，IOKit，BSD，Mach和一众没有画出来的东西组成了XNU内核。Mach作为一个微内核，其负责的内容包括处理器调度，**IPC（进程间通信）**和其它特别少量的功能。

​	在Mach中，所有的东西都是以对象的形式呈现的，而且这些对象之间还不能直接调用，只能够通过fafa



