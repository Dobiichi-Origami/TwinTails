# 引言

​	只是抱着想要拓展自己的语言能力和了解OC基础来写的这篇指南，不按照固定的思路去写，可能会很跳跃。如有错误，烦请指出，多多交流，谢谢

# Obejective-C的基础类型

​	在OC中，我们仍然可以使用类似于C中的各种基本类型，包括int char float和double等。但是在OC中还额外提供了一些别名，例如

+ NSInteger 是 long 的别称

  ![定义](https://github.com/Dobiichi-Origami/pics/blob/main/nsinteger-long.png)

+ CGFloat 是 double 的别称

  ![定义](https://github.com/Dobiichi-Origami/pics/blob/main/cgfloat-double.png)

​	这些基础类型，它们的使用和我们在 C/C++中的用法一致，故不再赘述。

​	我们同样可以在OC中使用各类集合类型，例如

+ NSArray / NSMutableArray
+ NSSet / NSMutableSet
+ NSDictionary / NSMutableDictionary

​	它们暴露出来的API都可以在`NSArray.h`，`NSSet.h` 和 `NSDictionary.h`中找到，有兴趣的同学可以自行阅读源码了解。Mutable与非Mutable之间最大的区别就在于带Mutable的集合对象其中的元素是可以被改变的。

# 在Objective-C 中构建自己的对象

​	OC作为一门面向对象的语言，它实现对象的语法也是相当有趣。

​	在OC中，所有对象都会被分为两个部分：

+ @interface 与 @end 包裹起来的部分，这里是声明对外暴露的方法与变量，类似于你在 Java 中声明为public的那部分。不需要去实现
+ @implemetation 与 @end 包裹起来的部分，这里用来负责实现类的各类方法。

看起来和写起来都很奇怪- -，但是写多了其实还好

## OC 中如何声明一个方法

​	在OC中，我们要声明一个方法，需要按照以下的格式去声明

​	 `-/+ (返回值)方法名:(参数1类型)参数1名字 :(参数2类型)参数2名字 ···;` 

​	其中  - 和 + 代表了其方法的类型，- 代表着实例函数，+ 代表着类函数。这个与其他语言是相类似的，方法的实现也是，只需要在@implementaion中实现即可。OC 不支持函数重载。

## OC 中如何在类中声明一个变量

​	OC不同于其他语言，在变量声明上有很多细节，以下面代码为例

```objective-c
@interface MyViewController :UIViewControlle
{
  UIButton *yourButton;	//这个是实例变量
  int count;	//这个是成员变量
  id data;	// 这个也是实例变量
}
@property (nonatomic, strong) UIButton *myButton; //这个叫属性变量
@end
```

​	以一对大括号 `{}` 括起来的是`成员变量`，成员变量中包括`实例变量`，区别在于实例变量是指向一种对象的成员变量。成员变量不会自动生成并实现 getter 与 setter 方法，也就是说它们相当于 Java 中声明为 private 的属性，除非你手动写api将它们暴露出来，否则它们对外界来说就是不可见的。

​	在大括号外面的，以 @property 为关键字的变量是`属性变量`，它们会自动生成对应的 getter 和 setter。

​	总结一下，在 OC 中，一个变量如果你不实现他对应的 setter 和 getter 方法，那么它对应的功能就不会向外界暴露，点语法其实也是调用它们的 getter 与 setter 方法，这里和其他语言的差别还是蛮大的。

### @property 和 @synthesize

​	@property 可以在`{}`外声明一个属性变量。在我们使用它的时候，@property 实际上做了以下两件事情

1. 在没有使用`@synthesize`时，声明一个属性，属性名为: _你的变量名。例如我的变量名叫 plus，那么它实际生成的是 _plus 这个属性。
2. 生成供外接读取的 getter 和 setter。以上文的 plus 为例，生成的 getter 叫做 plus，setter 叫做 setPlus（需要去掉前置的下划线）。这样子我们就可以通过点语法在外界访问它们。

​	@synthesize 是在 implementaion 和 @property 搭配使用的。其可以指定属性变量的实际实现。

​	例如这段代码 `@synthesize plus = nice`，我们在调用时，编译器不会自动生成 _plus 这个变量，而是去寻找定义中存不存在名为 nice 成员变量，如果不存在则生成一个；然后将二者绑定在一起。随后生成的 setPlus 与 plus 方法中会调用 nice 对象实现 setter 与 getter。我们用代码具体展示一下。

```objective-c
@interface OCDemo: NSObject
@property NSNumber *plus;
@end

@implementation OCDemo
@synthesize plus = nice;
// 当我们调用了@synthesize plus = nice时，实际上plus的 getter 和 setter 会变成以下模样，源代码里并看不见

- (NSNumber *)plus{
	return nice;
}

- (void)setPlus:(NSNumber *)number{
	nice = number;
  //如果你试图调用 _plus = number，你会发现你找不到这个变量
}

// 而原本应该是这样的

- (NSNumber *)plus{
	return _plus;
}

- (void)setPlus:(NSNumber *)number{
	_plus = number;
}

@end
```

​	这里，我们所声明的`nice` 是一个@private 修饰的对象，默认没有实现 getter 和 setter，需要用户手动实现。

### @property 中的参数

我们在声明属性变量时还可以使用参数来规范这个变量的一些特性，例如`@property (nonatomic)NSNumber *plus;`。常见的参数包括：

+ copy，增加引用计数，并且在指针指向的原对象的值发生改变时复制一份副本对象给该指针，保证值不会变。
+ strong，增加引用计数，表示持有该对象。（等同于MRC中的retain）
+ weak，不增加引用计数，弱引用。（等同于MRC中的assign）
  + 同时，C 语言的标准数据类型如 int，double 等以及 id 类型只能用 assign。
+ unsafe_unretained，与weak相同，区别可以见我的另一篇文章（[什么是ARC](https://github.com/Dobiichi-Origami/TwinTails/blob/master/iOS%E7%9B%B8%E5%85%B3/%E4%BB%80%E4%B9%88%E6%98%AF%20ARC.md)）

+ readwrite，产生 setter / getter方法
+ readonly，只产生简单的 getter，没有 setter。(此时重写 getter 方法时，不可以用下划线属性，比如 `_age`。必须先声明，比如：`@synthesize age = _age`，此时重写getter方法时才可以用_age)；
+ atomic，声明该属性在同一时刻只能被一条线程访问（相当于加锁，是默认参数之一）
+ nonatomic，atomic的反义词。

## Category 和 Extension

​	想为一个类声明Category，语法为：`@interface 添加的类名(添加的category名)`。以我上面所定义的 OCDemo 为例，就是 `@interface OCDemo(MyCategory)`。而要想声明Extension，则是 `@inteface 添加的类名()`。十分迷惑。category 和 extension 都需要在 @implementation 中实现函数，但每个category需要单独写一份 @implemention，而 extension 必须在主体中实现。一个类可以有多个extension和category。

​	Category 和 Extension 都可以向原本的类里添加方法，它们之间最大的区别在于前者是运行时决议的，而后者是被静态编译，成为类结构体的一部分的。这样的区别导致 Category 无法向原本的类中添加属性。具体原因我后面会再开另外一篇文章。

​	以下代码分别实现了 OCDemo 的一个 category 和 extension

```objective-c
@interface OCDemo: NSObject //原来的声明
@property NSNumber *plus;
@end

@interface OCDemo()	//extension
- (void)printExtension;
@end

@implementation OCDemo
@synthesize plus = nice;

- (NSNumber *)plus{
    return nice;
}

- (void)setPlus:(NSNumber *)number{
    nice = number;
}

- (void)printExtension { //extension 的实现
    NSLog(@"extension");
}

@end

@interface OCDemo(MyCategory) //category
- (void)printCategory;
@end

@implementation OCDemo(MyCategory) //category 的实现
- (void)printCategory{
    NSLog(@"Category");
}
@end

```

# @ 符号

​	这个符号其实类似于我们在 C 中经常能看见的**宏**。在OC中，@可以接收格式化字符串或者是数值类型，将他们分别生成为 NSString 或 NSNumber 的对象。这样子的原因是有的函数只能接受 NSString 或者 NSNumber 作为参数（毕竟面向对象），`NSLog()` 就是一个良好的例子：

![NSLog的定义](https://github.com/Dobiichi-Origami/pics/blob/main/nslog.png)

# 下午考试，还没写完，晚上再说。

