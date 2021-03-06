# 如何理解Swift的GCD

## iOS开发中的多线程表现形式

​	iOS开发中存在有多种实现多线程的方式，如

> * Pthreads
> * NSThread
> * GCD (General Central Dispatch)
> * NSOperation & NSOperationQueue

​	其中pthread是一个遵从POSIX标准的操作系统所提供的底层系统调用，也就是说这个Syscall你可以在MacOS，iOS哪怕是WatchOS上都可以用，包括Unix\Linux也是一样。

​	不过作为一个纯C加汇编实现的底层函数，这里不做任何讨论。

​	NSThread是由水果所封装的一个直接面向线程对象的解决方案，因为可以直接对线程直接进行操作，所以使用者可以很直观的对其进行使用，自主决定线程的每一个生命周期；不过这既是优点，也是缺点。因为要手动管理线程，操作和使用会变得相当麻烦，一般我们不用。

​	NSOperation这一套是水果对GCD的再度封装，但是我不懂，以后再说。

​	接下来我们谈一谈Swift中的GCD

## GCD in Swift

​	GCD作为水果首推的多线程解决方案，简单易用上手难度低（优点同样是缺点）。要理解GCD，需要慢慢仔细体会几个关键点：

### 到底是队列在执行任务还是线程在执行任务？

​	在水果的定义中，队列的名字是DispatchQueue，即调度队列。很明显，调度队列是用来调度『任务』用的，调度给谁执行？给线程执行。在整个GCD的体系中，队列是作为用户使用线程执行代码的媒介存在，负责对用户压入的任务进行调度，按照一定的规则『安排』任务到线程中执行（取决于队列类型和『安排的方法』）。线程本质上只管执行由队列所调度给他的任务，而不管这些任务是哪里来、怎么来的。我们研究的对象主要是队列。

### 如何理解async和sync

​	async和sync直观理解起来就是『异步』和『同步』的区别，这里的『异步』和『同步』都是相对于主线程来说的。当遇到async的代码块时，主线程可以直接fallthrough而不必等待async代码块回调，当遇到sync代码块时则相反，sync会阻塞队列，不让队列继续向下fallthrough，队列只有在执行完sync代码块之后才会继续调度。看起来相当符合人类的思维直觉。但是从不同的角度来讲，async和sync也可以被认为代表的是**创建线程的是与否**（取决于在串行队列还是并行队列中调用）

​	*对于串行队列（除主队列外）来说*：串行队列在**首次**调度async的代码块时，会向系统申请一条且只有一条线程，并且将这项异步任务丢进这条线程中执行；后续压入队列的异步任务最终也会被调度进这个线程中执行，不过必须等待其中正在执行的异步任务执行完毕。而在串行队列中执行sync代码块时，该队列会将任务调度进***主线程***中执行，不会额外再申请多余的线程。

​	*对于并行队列来说*：并行队列在调度async的代码块时，会在线程池中要么申请一条新线程，要么调度进已经存在的线程中（根据使用设备的不同，一个队列的线程池中最多可以最多可以存在64条线程），通过cpu对线程的调度实现并行操作。而在并行队列中执行sync代码块时，这些同步任务也会被并行队列调度进***主线程***中执行。

### 什么是主队列 (DispatchQueue.main) 和全局队列 (DispatchQueue.global() ) ？

​	全局队列是由系统创建的一条并行队列，其对用户是默认可用的，对于体量比较小的项目来说用全局队列就可以一般满足多线程的需求。相对复杂的是主队列。

​	*主队列*是由系统创建的，在应用运行之初就存在的一条串行队列。UIKit的所有操作***以及未指定线程的用户命令***都是在这条队列中进行异步调度的。主队列不同于普通串行队列的地方在于，其在调用async代码块时申请创建的线程是***主线程***，不会再有其他的线程可供调用，而且在主队列中接受调度的任务都是异步任务。这样的特性意味着如果你**往主队列中放入同步任务，就会因为出现队列的死锁而导致整个应用直接假死**。

### 主队列死锁

​	就像这样

```swift
func function(){
  let queue = DispatchQueue.main
  queue.sync{
    '你的代码块'
  }
}
```

​	调用这个函数时，xcode的编译器就会报出异常

​	死锁其实是一种争夺资源而导致的互相等待的现象。要想明白为什么会产生主队列死锁，我们先需要明确死锁产生的四个条件

> * **互斥条件：**所谓互斥就是进程在某一时间内独占资源，其他进程不可使用。
> * **请求与保持条件：**一个进程因请求资源而阻塞时，对已获得的资源保持不放。
> * **不剥夺条件：**进程已获得资源，在末使用完之前，不能强行剥夺。
> * **循环等待条件：**进程之间形成一种头尾相接的循环等待资源关系。

​	明确了这些条件之后，我们再针对上面的代码进行分析。

​	主线程死锁存在两方面的原因。我们假设function()为对象A，被调用的代码块为对象B。在不指定的情况下，对象A默认被主队列以async方式所调度，运行在主线程中。此时我们调用主队列对象，并且在主队列中用sync的方式压入对象B。***一方面，当B被调用时，由于主队列的特性，其任务被安排在主线程中运行，等待主线程空闲的时候插入其中运行。但现在主线程正被对象A所把持，由于sync代码块必须回调后原操作才能继续进行的缘故，对象A一直在等待对象B的执行（循环等待条件），如果对象B不执行，对象A也无法释放手头的资源（请求与保持条件），就这样两个对象一直无休止的互相等待下去，A等B运行，B等A放资源给B运行，但是A就是不放，最终形成了主线程死锁。另一方面，主队列作为一个串行队列，一次仅能允许一个任务被调度执行，不允许两个任务抢着执行。***

​	我们再换个角度想：*为什么在主线程中调用async不会出现死锁的现象？*

​	主队列作为一个串行队列，一次只能允许调度执行一项任务。当主队列调度到一个sync任务时，其必须进入sync代码块中执行，从而出现死锁。而如果调度的是async任务的话，虽然也需要执行async代码块，但是由于异步处理的关系，主队列可以跳过这个async代码块，等待主线程中的异步任务执行完毕以后，再倒回来执行这个代码块，我们可以用以下代码进行实验

```swift
let queue = DispatchQueue.main
queue.async{
  queue.async{
    for num in 11...15{
      print(num)
    }
  }
  fot num in 0...5{
    print(num)
  }
}
```

​	实验结果（此处省略）表明，程序是先打印出来0到5的数字，再打印出来的11到15的数字，印证了我们的结论，这也从另一个侧面表明了串行队列在执行嵌套代码块时的FIFO结构。

## 死锁

​	理解了主线程死锁以及为什么异步任务不会产生死锁的原因之后，要理解其他自定义队列中的死锁情况就容易的多了

```swift
let serialQueue = DispatchQueue(label: "serial")
//死锁1，在普通串行队列的sync代码块中嵌套sync代码块
serialQueue.sync {
    print("同步执行  thread: \(Thread.current)")
    serialQueue.sync {
        print("同步执行  thread: \(Thread.current)")
    }
}
//死锁2，在普通串行队列的async代码块中嵌套sync代码块
serialQueue.async {
    print("异步执行  thread: \(Thread.current)")
    serialQueue.sync {
        print("同步执行  thread: \(Thread.current)")
    }
}
```

​	总的来说，这两种死锁情况都是由于试图在一条串行队列中同时执行两项任务造成的。其中死锁1还存在着互相争夺线程资源的问题，较好理解。

​	但是以下这种情况并不会出现死锁

```swift
//自定义并行队列（全局队列结果相同）
let concurrentQueue = DispatchQueue(label: "concurrent", attributes: .concurrent)
//不会引起死锁
concurrentQueue.sync {
    print("同步执行  thread: \(Thread.current)")
    concurrentQueue.sync {
        print("同步执行  thread: \(Thread.current)")
    }
}
```

​	在并行队列中，队列的调度允许嵌套在外层的sync块放弃对主线程的锁，使得内层的sync块得以获取到资源从而继续执行，总体上呈现出顺序执行的特点。

## 重新总结串/并行队列

串行队列：同时仅允许一份任务被调度并获取线程资源。无论同步还是异步，严格按照FIFO的顺序对其进行执行，不存在有两个及以上的任务同时执行的情况。

并行队列：如果遇到异步任务，会在线程池中寻找可用线程并且将它丢给线程自由运行，然后fallthrough到队列中的下一个任务继续进行调度；如果遇到同步任务，将会阻塞该队列，直到同步任务执行完毕。

# DispatchGroup（调度组）

​	通过上面的循环嵌套同步/异步调用的方法，可以解决绝大多数现实开发中所遇到的问题。但是这种嵌套式的写法总归还是不甚美观与繁琐，为了用美观的方法去实现相同的功能，我们可以使用调度组来实现。

​	调度组是用来组织和管理多项待执行任务用的一种结构，下面先写出两种常用的调度组函数

```swift
let group = DispatchGroup()
group.notify(queue: queueWhereYouWantToExecuteCode){closure}
// notify()函数可以在组内所有的任务都被执行完之后异步调用，在参数所指定的DispatchQueue中异步执行闭包中的代码
group.wait(timeout: TimeInterval)
// wait()函数在被调用时会阻塞当前执行队列，阻塞时间长短由参数决定，缺省为无限期。在达到预设阻塞时间或任务在预定时间内完成时会返回一个enum，代表了任务的完成或超时。
```

​	调度组的出现，允许我们更加直观和简洁的完成我们的任务。以同时进行两次异步网络调用后刷新UI的例子举例

​	在不使用DispatchGroup的情况下，我们是这么写的：

```swift
let queue = DispatchQueue(label: "concurrent", attributes: .concurrent)

queue.async{
  queue.async{
    /* 在这里执行你的网络请求 */
    DispatchQueue.main.async{
    	/* 执行UI刷新 */
  	}
  }
  /* 在这里执行你的网络请求 */
}
```

​	在使用了DispatchGroup以后，我们可以改为这么写：

```swift
let queue = DispatchQueue(label: "concurrent", attributes: .concurrent)
let group = DispatchGroup()

queue.async(group: group){
  /* 在这里执行你的网络请求 */
}

queue.async(group: group){
  /* 在这里执行你的网络请求 */
}

print("开始监听")

group.notify(queue: DispatchQueue.main){
  /* 执行UI刷新 */
}

/* group.wait()
	如果你想的话还可以在这里阻塞主队列，等待任务执行完毕后解除阻塞 */

print("监听完毕")
```

​	对比两种写法的代码，后者在代码可读性和可维护性上好于前者，尤其是在嵌套情况相当多的时候，虽然两者在运行上的效果基本一致，取决于开发者的偏好，并不存在真正的高下之分。

#  .barrier

​	为了管理线程的运行状态，除了上面的调度组以外，我们还有信号量以及.barrier可以满足我们的需求。

​	在DispatchWorkItem的构造函数中，我们除了可以定义闭包内容以外，还可以设置其中的flag参数为.barrier。设置了.barrier的DispatchWorkItem在被调用到时并不会立即执行，而是等待当前队列中正在执行的所有DispatchWorkItem全部执行完之后再单独执行，单独执行完后再正常进行余下的内容调用。以下代码可以演示相关效果，此处不再赘述：

```swift
let item1 = DispatchWorkItem {
   // 执行内容
}

let item2 = DispatchWorkItem {
   // 执行内容
}

//给item3任务加barrier标识
let item3 = DispatchWorkItem(flags: .barrier) {
   // 执行内容
}

let item4 = DispatchWorkItem {
	// 执行内容
}

let item5 = DispatchWorkItem {
	// 执行内容
}

let queue = DispatchQueue(label: "test", attributes: .concurrent)
queue.async(execute: item1)
queue.async(execute: item2)
queue.async(execute: item3)
queue.async(execute: item4)
queue.async(execute: item5)
```

设置flag为.barrier的方式对全局队列不生效，原因有待深入研究。对串行队列使用.barrier没有意义，在并行队列中使用sync代码块可以达到相同的效果，只不过该任务将被放入主线程中执行，需要用户酌情考量。

# DispatchSemaphore（信号量）

​	信号量这个名称不知道是何人翻译的，初看并不是那么直观易于理解。

​	DispatchSemaphore更像是用来控制流量的节流阀，用来控制同时执行的任务数量。以下代码可以初始化一个DispatchSemaphore

```swift
let semaphore = DispatchSemaphore(value: valueYouWant)
```

​	有了这个DispatchSemaphore之后，我们就可以将其嵌入到队列的闭包之中，实现对队列并发执行任务数量的精准控制。我们以打印一个九九乘法表为例

```swift
let semaphore = DispatchSemaphore(value: 1)
let queue = DispatchQueue(label: "concurrent", attribute: .concurrent)

for i in 1...9{
  queue.async{
    semaphore.wait()
    var str = ""
    for j in 1...9{
      let value = i*j
      let tempStr = value <= 9 ? " \(value)  " : "\(value)  "
      str += tempStr
    }
    print(str)
    semaphore.signal()
  }
}
```

