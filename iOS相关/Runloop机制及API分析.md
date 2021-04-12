[TOC]

# 引言

​	这块内容涉及到的知识点相当之多，建议读者在阅读本文时在Playground中多运行代码，加以实践，配合苹果官方的文档（强烈推荐）和网络上其他文章辅助理解。

# 什么是Runloop

​	Runloop是一种事件处理机制和对象，它可以监听整个Runloop对象内部所拥有的计时器（TImer）和事件源（Source），当这两者的事件触发（包括但不限于收到来自外部的输入，计时器到时）时，Runloop就会调用其相关的Thread来处理这些事件，可以实现对线程资源的持久利用。我们的主线程出生就自带有一个Runloop，用来处理应用生命周期中的各类事件，就像一个loop（循环）不停的run（运行）下去，下面是网上被用的很多的一张表示Runloop运行过程的图

<img src="https://upload-images.jianshu.io/upload_images/143845-ca739f2c626694de.png" alt="img" style="zoom: 50%;" />

​	第一次看这个图可能会对其中的各种名词感到迷惑和不知所措，我们先讲其中的组成部分，最后再倒回来看看这个是怎么一回事。

# Runloop和线程

​	Runloop的存在依托于线程Thread，它利用Thread的计算资源来处理它所接收到的各类事务。一般情况下，以NSThread为例，NSThread在运行完自身的任务后就会退出；如果使用了Runloop，则NSThread会在Runloop退出之前一直存在，实现了NSThread的持久化，可以用于应对一众需要线程长时间存活的业务情况，经典的例子就是AFNetworking 2.x版本的实现；它利用Runloop实现了一条持久化线程，用以初始化网络请求，并且接受来自服务器的响应。

# Runloop的相关类

​	Runloop在swift中的实现有两个，Runloop和CFRunloop，前者是对后者的包装，而后者是CoreFoundation框架内的，提供纯C函数API的实现。本文以CFRunloop为示例API，感兴趣的读者请自行查阅Runloop API进行学习

​	所有CFRunLoop中的函数和类，都是以CFRunLoop开头的名字。在CFRunloop中，我们一般会接触到以下五种对象

+ CFRunLoop —— 对应一个Runloop对象

+ CFRunLoopMode ——Runloop模式，代表了Runloop中会出现的运行模式

+ CFRunLoopSource —— Runloop事件源，分为source0和source1两种，可以根据需要向Runloop发送事件信号以唤醒Runloop

+ CFRunLoopTimer —— Runloop计时器，顾名思义，可以在Runloop中定时发送信号唤醒Runloop

+ CFRunLoopObserver —— Runloop监视器，可以监视整个Runloop中一个或多个阶段的状态变化，并且能根据用户设定做出相应的操作

  接下来，文章会分类讲解这五个对象

## CFRunLoop

​	作为Runloop的一个核心类，CFRunLoop对象只能由工厂模式生产。想要获取到主线程的Runloop，可以调用``CFRunLoopGetMain()`，想在一个自定义的子线程中获取到专属CFRunLoop对象，只需要在子线程的方法闭包中调用`CFRunLoopGetCurrent()`即可。在调用该方法之前，线程中不存在CFRunLoop对象，自然也就没有Runloop的说法。调用时系统会自动创建一个CFRunLoop对象，并且将该对象与当前子线程绑定，之后再调用`CFRunLoopGetCurrent()`只会获取到当前已有的CFRunLoop对象，有兴趣的读者可以执行以下代码看看结果。

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
  
  > 在swift的Core Fundation中只能找到defaultMode和commonModes两种模式，如果有人知道这是怎么一回事还请多多指教

​	每个CFRunLoop对象都拥有一个或多个运行模式，我们在向CFRunLoop添加各类事件源、计时器和监视器时都需要指定运行模式，本质上就是在向CFRunLoop对象中的各类模式添加。想知道当前Runloop具有什么样的运行模式，可以使用`CFRunLoopCopyAllModes(rl: CFRunLoop!)`获得到包含当前Runloop所有运行模式的数组，如果想要切换Runloop的运行模式，则必须先停止Runloop，再重新指定运行模式开始运行。

​	Runloop在启动时，必须指定其中一种运行模式，且指定的运行模式中必须存在有Source和Timer，否则整个Runloop会直接退出。

​	这里要重点讲一下**kCFRunLoopCommonModes**这个模式，我们暂且称之为普通模式。正如上面所讲，普通模式并不是一种具体的模式，而是一个或多个其它模式的集合。CFRunLoop无法运行在这种模式下，但是Source，Timer和Observer都可以添加到该模式下，相当于允许这些Item在多个模式中运行，当CFRunLoop的模式发生切换以后它们仍然可以继续运行。因为我们的应用时刻会在模式间切换（最常见的就是在kCFRunLoopDefaultMode和UITrackingRunLoopMode两种模式之间切换），如果你想让一个Item持续工作，那你就得将它添加到普通模式中。普通模式中所包含的模式不是一成不变的，可以通过调用函数 `CFRunLoopAddCommonMode(_ rl: CFRunLoop!, _ mode: CFRunLoopMode!)` 来向特定Runloop中的普通模式里添加你想要的模式

## CFRunLoopSource

​	CFRunLoopSource的存在允许用户和系统在一定条件下，向Runloop发送事件信号，让RunLoop对其进行处理。

​	按照水果开发文档的划分，我们可以将CFRunLoopSource分为两类：

1. Version 0（Source 0）—— 非基于mach_port的事件源
2. Version 1（Source 1）—— 基于mach_port的事件源

​	在解释Source 0和Source 1的区别之前，我想先说一下这个mach_port是个什么东西。

### 什么是mach_port

​	在iOS和MacOS中，其操作底层核心为Darwin，它包括了诸如系统内核，驱动和shell等等的内容。

<img src="https://blog.ibireme.com/wp-content/uploads/2015/05/RunLoop_4.png" alt="img" style="zoom:50%;" />

​	上图给出了Darwin核心的内部结构。其中，IOKit，BSD，Mach和一众没有画出来的东西组成了XNU内核。Mach作为一个微内核，其负责的内容包括处理器调度，**IPC（进程间通信）**和其它特别少量的功能。

​	在Mach中，所有的东西像是进程、线程、虚拟内存等都是以对象的形式呈现的，而且这些对象之间还不能直接调用，只能够通过**消息**的方式在对象之间互相通信，而这种通信涉及到了mach_port，对象A向对象B的mach_port发送消息，对象B在收到消息之后就可以做出相关的反应。我们的Runloop内部也使用了mach_port实现了类似的消息发送/接收机制。

### mach_port在Runloop中的应用

​	现在我们再倒回来看，根据CFRunloop的内部实现，Runloop在休眠时调用了 `mach_msg()` 函数，令runloop等待并监听发送到自身mach_port的消息，如果有了来自外面的消息，它就会被唤醒并开始处理任务，这些消息可以来自：

+ Source 1 事件源
+ Timer 到了设定时间
+ 被用户调用`CFRunLoopWakeUp(_ rl: CFRunLoop!)`手动唤醒
+ Runloop自身超时了（如果你用的是`CFRunLoopRunInMode(_ mode: CFRunLoopMode!, _ seconds: CFTimeInterval, _ returnAfterSourceHandled: Bool)`来启动Runloop的话）

​	其中能够自主唤醒Runloop的事件源只有来自Source 1的事件，因为两个事件源中只有它实现了mach_port相关内容，可以直接向Runloop发送消息，而Source 0则不行，需要用户手动唤醒Runloop。这就是它们两者之间的本质区别。一般情况下我们不会自行创建Source 1事件源，苹果官方也不鼓励你自行使用mach相关API。

###Source 1和Source 0

​	Source 1事件源通常作为来自硬件的消息的中间转发者而出现。举个例子，当我们触碰屏幕时，系统内核会通过mach_port发送一个触碰事件相关的Event给Source 1事件源，Source 1将这个Event打包成一个Source 0事件源，加入主线程的Runloop中并打上待处理标记后唤醒Runloop，将任务交由Runloop处理。

​	Source 0则是我们可以自由创建的事件源，调用`CFRunLoopSourceCreate(_ allocator: CFAllocator!, _ order: CFIndex, _ context: UnsafeMutablePointer<CFRunLoopSourceContext>!)`即可创建。我们可以看到，这个函数的参数中要求一个CFRunloopSourceContext的结构体指针对象，这个对象规定了我们Source的一系列属性和行为，其中最重要也是最常用的的就是 schedule，perform和cancel三个回调，它们分别规定了source 0在被**加入**Runloop时，被Runloop**执行**时和被Runloop**移出**时会进行的操作。顺带一提，还有一个名为CFRunloopSourceContext1的结构体，这是给Source 1所使用的上下文对象，和上文所提到的Source 0的结构体的差别仅在于其多了一个成员变量 `getPort: ((UnsafeMutableRawPointer?) -> mach_port_t)!`，用来获取Source 1相关的mach_port。

​	在创建好了Source之后，利用函数`CFRunLoopAddSource(_ rl: CFRunLoop!, _ source: CFRunLoopSource!, _ mode: CFRunLoopMode!)`就可以将Source添加到特定Runloop下的某个模式了

## CFRunLoopTimer

​	顾名思义，CFRunLoopTimer是一个计时器对象。添加到特定Runloop并且在预设时间到期以后就会向Runloop发消息以激活Runloop，并且由Runloop执行其中特定的回调。

​	由于CFRunLoopTimer与Timer是共通的，所以我们可以用Timer添加到Runloop中。Timer类中又分为两种：

1. Timer —— 就是普通的Timer，可以通过构造函数创建
2. scheduledTimer —— 只能通过工厂模式创建，且创建之后会被自动添加到当前线程Runloop的defaultMode中

## CFRunLoopObserver

​	在整个运行过程中，Runloop会在多种运行状态之间来回转换，CFRunLoopObserver可以接收到来自Runloop的状态转换通知，并且根据用户的设定就一种或多种状态做出反应。Apple在CFRunLoopActivity中以静态属性的形式列出了Runloop生命周期中可供Observer监听的所有状态：

```swift
static var entry: CFRunLoopActivity
// 即将进入Runloop，对应的值为 1<<0 == 1

static var beforeTimers: CFRunLoopActivity
// 即将处理Timers，对应的值为 1<<1 == 2

static var beforeSources: CFRunLoopActivity
// 即将处理Sources，对应的值为 1<<2 == 4

static var beforeWaiting: CFRunLoopActivity
// 即将进入休眠状态，对应的值为 1<<5 == 32

static var afterWaiting: CFRunLoopActivity
// 刚结束休眠状态，对应的值为 1<<6 == 64

static var exit: CFRunLoopActivity
// 即将退出Runloop，对应的值为 1<<7 == 128

static var allActivities: CFRunLoopActivity
// 监听以上所有状态，对应的值为 0x0FFFFFFF == 268435455
```

​	我们可以通过两种方式创建CFRunLoopObserver，一种是，利用函数 `CFRunLoopObserverCreateWithHandler(_ allocator: CFAllocator!, _ activities: CFOptionFlags, _ repeats: Bool, _ order: CFIndex, _ block: ((CFRunLoopObserver?, CFRunLoopActivity) -> Void)!)` 通过闭包的方式创建。另一种是利用函数 `CFRunLoopObserverCreate(_ allocator: CFAllocator!, _ activities: CFOptionFlags, _ repeats: Bool, _ order: CFIndex, _ callout: CFRunLoopObserverCallBack!, _ context: UnsafeMutablePointer<CFRunLoopObserverContext>!)` 通过CFRunLoopObserverContext 监视器上下文的方式来创建，这种创建方式就类似于我们之前创建Source 0 事件源，可以迁移一下。

​	创建好CFRunLoopObserver之后，利用函数 `CFRunLoopAddObserver(_ rl: CFRunLoop!, _ observer: CFRunLoopObserver!, _ mode: CFRunLoopMode!)` 就可以添加到你想要的RunloopMode中监视你想要的活动状态。

# RunLoop的运行过程

​	讲完了RunLoop的相关类，我们再倒回来看看一开始我们所提到的运行过程的图

<img src="https://upload-images.jianshu.io/upload_images/143845-ca739f2c626694de.png" alt="img" style="zoom: 50%;" />

​	我们提几个重要的点。

1. 在启动Runloop时，有两种方法

   1. `CFRunLoopRun()` 以DefaultMode启动Runloop，不限运行时间和处理次数，除非手动调用 `CFRunLoopStop(_ rl: CFRunLoop!)` 停止RunLoop。
2. `CFRunLoopRunInMode(_ mode: CFRunLoopMode!, _ seconds: CFTimeInterval, _ returnAfterSourceHandled: Bool)` 以指定模式启动RunLoop，在超出设定的运行时间后停止。如果指定returnAfterSourceHandled为true或超时时间为0，则只会处理一项任务，然后立刻退出（也有例外，如果超时时间为0且待处理的任务中存在一项来自Source 0的事件，则可能会处理两项）
2. Runloop不能在没有Source和Timer的mode中运行，否则会当场退出
3. 虽然在进入Runloop后第一步就是通知Observer Runloop即将处理Timer，但是实际上Timer中的任务的处理是发生在图上第九步的，因为只有Timer到时间之后，它才会发送相应的信息给Runloop请求处理。
4. Runloop的运行/休眠状态切换涉及到用户态到内核态的转换（`mach_msg()`本身就是个系统调用），引申出来在iOS和MacOS中进程间通信都必须经过内核转发。