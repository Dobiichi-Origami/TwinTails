[TOC]

# 什么是 ARC

​	在 Java 中，由于有 GC 机制的关系，使得用户可以无需在意内存回收的问题，并将它们全部交与 JVM 来处理。类似的，在iOS中存在一套简单易行的内存回收机制——自动引用计数（Auto Reference Counter），通过对象的引用计数，实现计数为零时调用对象的析构函数回收内存。

​	引用一共有三种类型，分别是**强引用（strong）**、**弱引用（weak）**和**未拥有（unowned）**，本文以Swift为演示语言。

# 计数器

​	每个对象在被实例化创建出来以后便会持有一个计数器（Counter），这个Counter记录了对象被**强引用**的次数。如上文所言，当这个计数器的值归零时，持有这个计数器的对象即被销毁

# 强引用

​	一般情况下，普通的let或var引用即为强引用。将某个对象赋值给强引用会使得对象的引用计数 +1；反之，在该引用被指向其它对象或置为nil时，该对象的引用计数 -1。以以下代码为例

```swift
import UIKit

class Person{
    var name:String
    var apartment:Apartment?
    
    init(name: String) {
        self.name = name
        print("构造了一个人：\(name)")
    }
    
    deinit {
        print("销毁了一个人：\(name)")
    }
}

class Apartment{
    var number:Int
    var people:Person?
    
    init(number:Int){
        self.number = number
        print("房间\(number)被构造了")
    }
    
    deinit {
        print("房间\(number)销毁了")
    }
}

print("构造对象")
var person1:Person? = Person(name: "Lisa")
var apartment1:Apartment? = Apartment(number: 1)

print("销毁对象")
person1 = nil
apartment1 = nil
print("销毁完成")
```

​	调用该代码，会发现代表Person和Apartment的两个实例对象先后被创造并随后被销毁。

## 循环引用

​	强引用看起来不错，但是有一个小问题，当我们将person1赋值给apartment1的people属性并且将apartment1赋值给person1的apartment属性后，再置二者的引用为nil，发现这两者的析构函数并没有被调用

> 在上面代码的基础上加上以下两行代码
>
> ```swift
> person1?.apartment = apartment1
> apartment1?.people = person1
> ```

​		其中的原因是，两个实例中关于彼此的属性其实也是强引用的一种，将对象赋值给这些属性也会使得计数器的值 +1，从而形成了循环引用（Cycle Reference）。循环引用指的是两个对象彼此互相持有对对方的引用，使得强引用计数器的值无法归零，而导致两者所占内存空间无法被释放的问题。为了解决这个问题，我们可以利用weak和unowned两种引用类型

# weak和unowned

​	weak 和unowned 两种引用，既存在相同的部分，又不存在不同的地方。我们先说两者相同的地方

​	weak和 unowned 两者都是弱引用，加上这两者的引用不会使被引用对象的计数器 +1。

​	我们将上面的代码稍微做一点改动，只需要在 `  var apartment:Apartment?` 或 `  var people:Person?` 两个属性中的其中一个前面加上 weak 或 unowned 就可以解决循环引用的问题。

> ​	以上面的代码为例，假设我们将 `var apartment:Apartment?` 加上 weak 前缀，执行上述代码，在销毁之前，apartment1 指向的对象的引用计数只为1，而person1 指向的对象为2。在我们将 apartment1 置为 nil 之后，apartment1 的对象被释放，同时该对象持有的对 person1 的强引用也被释放，person1 的对象的引用计数降为1。

​	接下来再说说两者之间的不同点。

​	weak 和unowned 之间的最大不同就在于引用是否会在对象被销毁时指向 nil

​	weak 引用的对象如果被释放，引用该对象的引用也会被 ARC 自动置为 nil ；而 unowned ，根据 Swift 的要求，所修饰的引用必须明确指向一个实例对象，这也导致 ARC 不会在该引用指向的对象被销毁时将引用指向nil，如果你在销毁了这个引用的对象再透过引用去访问就会导致崩溃，类似于 C/C++ 中指向非法内存的指针，所以以 unowned 修饰的引用从始至终都不得为 nil。

​	这样的区别可以引出以下的想法——以 unowned 修饰的被引用客体，在引用主体被销毁之前必须一直存在。就类似于一个从属关系，被 unowned 引用的对象 “拥有” 引用该对象的对象，下级对象可以被随时销毁，而上级对象必须持续存在以“拥有”下级对象。

