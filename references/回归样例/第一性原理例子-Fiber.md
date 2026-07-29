# Fiber

# Fiber 架构 

## 1\. 最终目的

**设计一个可中断续渲染，高效率，高鲁棒性的渲染架构。**

## 2\. 目前现状与要解决的问题

### 渲染任务同步且无法中断，重渲染任务100%阻塞I/O和JS执行，无法调节任务优先级

现状：

- **主线程互斥执行**：浏览器主线程同一时间只能处理一类主要任务。JS 执行、样式计算、布局、绘制、用户输入响应都会争夺主线程时间。

- **帧预算有限**：60 FPS 下，一帧大约只有 16\.7ms。一次更新任务过长，就会挤占输入响应和浏览器绘制时间，用户感知就是卡顿。

- **渲染任务同步且无法中断**：React 组件本质上形成树。一次状态变化后，React 会走更新触发、递归渲染/调和、DOM 提交这条基本链路；旧 Stack Reconciler 依赖同步递归执行，Render/Reconciliation 过程缺少可中断、可恢复、可按优先级调度的能力。

    ##### 例子：

    ```Markdown
    App
    └── SearchPage
        ├── SearchInput
        └── BigList
            ├── Item 1
            ├── Item 2
            ├── ...
            └── Item 10000
    ```

Fiber 之前，React 的核心遍历方式更接近普通递归函数调用。它会从根节点开始，一层层往下执行：

```JavaScript
function work(component) {
  const children = component.render();

  for (const child of children) {
    work(child);
  }
}
```

用户输入 → 触发 `setState` → React 开始更新 `App` → 更新 `SearchPage` → 更新 `SearchInput` → 更新 `BigList` → 更新 `Item 1` → 更新 `Item 2` → 一直更新到 `Item 10000` → 算完所有变化 → 一次性提交 DOM。

**没有设计中断、保留进度信息、断点续渲染的方案，进度信息只在执行中的 JS 原生调用栈存在。**

**一旦开始递归计算，就必须把这次计算同步跑完。跑完之前，浏览器不能及时处理新的输入回调、React 也不能优先处理更紧急的更新。**

问题：

- **重渲染任务100%阻塞I/O和JS执行，无法调节任务优先级**：早期 Stack Reconciler 依赖 JS 调用栈递归遍历组件树。一旦开始，就必须一路执行到底，中途无法安全暂停。如果用户正在输入，但页面同时触发了大列表重渲染。如果重渲染任务占用主线程，输入反馈会延迟。

    - **Diff 再快也可能卡**：React 使用启发式 O\(n\) diff，避免了通用树编辑距离算法 O\(n³\) 的高成本；但当节点数量足够大时，O\(n\) 任务仍然可能超过单帧预算。\([legacy\.reactjs\.org](https://legacy.reactjs.org/docs/reconciliation.html)\)



---

## 3\. 采用的方案

Fiber 的核心方案，是把 React 的 Render / Reconciliation 从同步递归执行，改造成可保存进度、可分片推进、可按优先级调度、可丢弃未提交结果、可集中提交的任务系统。

整体执行链路可以压缩成：

```Plain Text
setState
  ↓
创建 update
  ↓
写入 Fiber.updateQueue
  ↓
分配 lane
  ↓
lane 冒泡到 root
  ↓
创建 workInProgress tree
  ↓
进入 workLoop
  ↓
beginWork 向下计算
  ↓
completeWork 向上收集副作用
  ↓
Render 完成生成 finishedWork
  ↓
Commit 同步提交 DOM
  ↓
finishedWork 成为新的 current tree
```

---

### 3\.1 Fiber 工作单元：把组件节点改造成可保存进度的任务记录

**从隐式调用栈到显式任务记录：** 旧 Stack Reconciler 的进度主要保存在 JS 原生调用栈里，一旦递归开始，React 很难在中途安全暂停、恢复或改道处理更高优先级任务。要让渲染过程可中断，React 需要把“当前处理到哪个节点、父节点是谁、下一个兄弟节点是谁、本轮更新是什么、后续需要提交什么”从调用栈中抽出来，变成自己可读写的数据结构。Fiber 节点因此成为 React 的最小工作单元，它既表示 UI 节点，也表示一份可调度、可恢复、可提交的任务记录。

#### 核心机制

##### 节点身份：保存复用判断所需信息

Fiber 首先记录“这个节点是谁”，因为 Reconciliation 需要判断旧节点能否复用。

- `type` 表示组件类型或 DOM 类型。

    - 函数组件、类组件、原生 DOM 节点会形成不同类型的 Fiber。

- `key` 用于列表场景下的稳定身份判断。

    - 同一层级的列表节点需要通过 `key` 判断前后是否是同一个业务对象。

    - `key` 不稳定会导致错误复用或频繁重建。

- `type + key` 一致时，旧 Fiber 有复用基础。

    - 旧 Fiber 被复用时，组件状态和 DOM 引用可以保留。

    - 旧 Fiber 无法复用时，React 创建新 Fiber，并在后续 Commit 中处理插入或删除。

##### 节点关系：保存可恢复遍历路径

Fiber 用三个指针把树结构转成链式结构。

- `child` 指向第一个子 Fiber。

    - 当前节点进入子树时，React 优先处理 `child`。

- `sibling` 指向下一个兄弟 Fiber。

    - 当前节点没有子节点或子树处理完成后，React 尝试进入 `sibling`。

- `return` 指向父 Fiber。

    - 当前节点和兄弟节点都处理完成后，React 通过 `return` 回到父节点。

- `child / sibling / return` 共同替代 JS 调用栈里的隐式遍历路径。

    - 任务暂停后，React 仍然知道当前处理到哪里。

    - 任务恢复时，React 可以从保存的 Fiber 继续推进。

##### 状态输入：保存本轮计算所需上下文

Fiber 同时记录本轮输入和上轮已确认结果。

- `memoizedProps` 表示上轮已经确认的 props。

    - React 可以用它和 `pendingProps` 做对比，判断是否需要继续计算。

- `memoizedState` 表示上轮已经确认的 state。

    - 函数组件 Hooks 状态、类组件 state 最终都会反映到对应 Fiber 上。

- `pendingProps` 表示本轮收到的新 props。

    - `beginWork` 会根据它计算当前节点的新输出。

- `updateQueue` 保存本轮待处理的状态更新。

    - `setState`、Hook 更新等会进入对应 Fiber 的更新队列。

    - Render 阶段会根据当前 lanes 选择其中一部分 update 参与计算。

##### 更新队列：保存状态变化记录

一次 `setState` 会被包装成 update，并写入对应 Fiber 的 `updateQueue`。

```TypeScript
type Update = {
  lane: Lane;
  payload: any;
  next: Update | null;
};
```

- `payload` 表示状态变化内容。

    - 例如 `keyword = 'a'` 或 `listKeyword = 'a'`。

- `lane` 表示这次更新的优先级。

    - 高优先级 update 可以先参与本轮 Render。

    - 低优先级 update 可以留在队列中，后续再处理。

- `next` 串联多个 update。

    - 多次状态更新可以形成队列。

    - React 在 Render 阶段按当前 lanes 计算最终 state。

##### 优先级信息：保存当前节点和子树任务等级

Fiber 节点既记录自身更新，也记录子树更新。

- `lanes` 表示当前 Fiber 自身有哪些优先级更新。

    - 当前组件触发更新时，会把对应 lane 写入自身 Fiber。

- `childLanes` 表示子树里有哪些优先级更新。

    - 子 Fiber 有更新时，lane 会向父链冒泡。

    - 父 Fiber 可以通过 `childLanes` 判断当前优先级下是否需要进入某棵子树。

- root 聚合整棵树的 pending lanes。

    - 调度器从 root 选择下一批要处理的 lanes。

    - 高优先级 lanes 可以先进入 Render。

##### 副作用信息：保存 Commit 阶段的执行计划

Render 阶段只计算变化，真实 DOM 变更交给 Commit 阶段执行。

- `flags` 表示当前 Fiber 自身需要执行的副作用。

    - 例如插入、更新、删除、ref 处理。

- `subtreeFlags` 表示子树里存在副作用。

    - Commit 阶段可以借助它快速跳过无副作用子树。

- `deletions` 保存需要删除的子节点。

    - 删除节点需要在 Commit 阶段集中处理。

- 副作用信息在 Render 阶段收集，在 Commit 阶段消费。

    - Render 可以暂停和重做。

    - Commit 必须同步完成，保证真实 UI 一致。

##### 双缓存引用：连接当前树和工作树

Fiber 通过 `alternate` 连接 current Fiber 和 workInProgress Fiber。

- current Fiber 表示屏幕上已经提交的版本。

    - 它保存用户当前看到的 UI 状态。

- workInProgress Fiber 表示正在内存中计算的下一版。

    - Render 阶段的中间结果写入 workInProgress。

- `alternate` 连接两棵 Fiber。

    - 首次更新时创建 alternate。

    - 后续更新时复用 alternate，减少重复创建成本。

#### 模块实现例子

```TypeScript
type Fiber = {
  type: any;
  key: string | null;

  return: Fiber | null;
  child: Fiber | null;
  sibling: Fiber | null;

  pendingProps: any;
  memoizedProps: any;
  memoizedState: any;
  updateQueue: UpdateQueue | null;

  lanes: Lanes;
  childLanes: Lanes;

  flags: Flags;
  subtreeFlags: Flags;
  deletions: Fiber[] | null;

  alternate: Fiber | null;
};
```

一次搜索输入更新进入 Fiber 后，可以简化成：

```Plain Text
SearchPageFiber
  updateQueue:
    update(payload: keyword = 'a', lane: SyncLane)
    update(payload: listKeyword = 'a', lane: TransitionLane)

  lanes:
    SyncLane | TransitionLane

  childLanes:
    BigList 子树存在 TransitionLane 更新
```

这一层的本质是：React 用 Fiber 节点把渲染过程从“临时递归调用”改造成“可保存、可恢复、可调度、可提交的任务记录”。

---

### 3\.2 可恢复工作循环：把整棵树递归改造成单元化任务推进

**从递归控制权到 React 自控执行器：** Fiber 节点解决了“进度如何保存”的问题，但还需要一套执行器来决定每次处理哪个 Fiber、什么时候继续、什么时候暂停、暂停后从哪里恢复。旧递归模型的进入、返回和结束由 JS 调用栈控制，React 缺少稳定的暂停点。Fiber 架构改用 `nextUnitOfWork` 保存当前推进位置，用 `performUnitOfWork` 每次处理一个 Fiber，用 `shouldYield` 在工作单元之间判断是否让出主线程。大树更新因此从“一次性递归到底”变成“按 Fiber 单元逐步推进”。

#### 核心机制

##### workLoop：按时间预算推进 Fiber 任务

`workLoop` 是 Render 阶段的主执行循环。

```JavaScript
let nextUnitOfWork = rootFiber;

function workLoopConcurrent() {
  while (nextUnitOfWork !== null && !shouldYield()) {
    nextUnitOfWork = performUnitOfWork(nextUnitOfWork);
  }

  if (nextUnitOfWork !== null) {
    scheduleCallback(workLoopConcurrent);
  } else {
    commitRoot();
  }
}
```

- `nextUnitOfWork` 保存下一步要处理的 Fiber。

    - Render 暂停时，它就是恢复位置。

    - Render 继续时，React 从它指向的 Fiber 重新进入工作循环。

- `performUnitOfWork` 处理当前 Fiber，并返回下一个 Fiber。

    - 有子节点时返回 child。

    - 没有子节点时进入 complete 流程，寻找 sibling 或 return。

- `shouldYield` 判断当前执行是否需要让出主线程。

    - 时间片未耗尽时继续处理。

    - 时间片耗尽时暂停 Render，把控制权还给浏览器。

- `scheduleCallback` 负责安排剩余任务。

    - 未完成的 Render 后续继续执行。

    - 更高优先级任务也可以插队。

##### performUnitOfWork：把单个 Fiber 分成向下计算和向上收尾

每个 Fiber 的处理分成两段：`beginWork` 和 `completeWork`。

```JavaScript
function performUnitOfWork(fiber) {
  const child = beginWork(fiber);

  if (child !== null) {
    return child;
  }

  return completeUnitOfWork(fiber);
}
```

- `beginWork` 负责向下计算。

    - 读取当前 Fiber 的输入。

    - 计算新状态。

    - 生成或复用子 Fiber。

- `completeWork` 负责向上收尾。

    - 准备 DOM 更新信息。

    - 收集当前 Fiber 的副作用。

    - 汇总子树副作用。

- `performUnitOfWork` 连接两段流程。

    - 当前 Fiber 有子节点时继续向下。

    - 当前 Fiber 没有子节点时开始向上完成当前子树。

##### beginWork：向下计算子节点

`beginWork` 的职责是把当前 Fiber 的输入转成下一层 Fiber。

- 读取 `pendingProps`。

    - 本轮 props 变化会进入当前计算。

- 处理 `updateQueue`。

    - 根据当前 render lanes 选择对应 update。

    - 计算新的 `memoizedState`。

- 调用组件函数或类组件 render。

    - 得到新的 React Element。

- 执行 Reconciliation。

    - 判断旧子 Fiber 能否复用。

    - 创建、复用或标记删除子 Fiber。

- 返回第一个子 Fiber。

    - 工作循环继续向下处理子树。

##### completeWork：向上收尾并收集结果

当前 Fiber 的子节点处理完成后，React 进入 `completeWork`。

```JavaScript
function completeUnitOfWork(fiber) {
  let node = fiber;

  while (node !== null) {
    completeWork(node);

    if (node.sibling !== null) {
      return node.sibling;
    }

    node = node.return;
  }

  return null;
}
```

- `completeWork` 处理当前 Fiber 的收尾工作。

    - 对 DOM Fiber 准备属性更新。

    - 对文本节点准备文本更新。

    - 对新节点标记插入。

- `sibling` 决定是否进入兄弟节点。

    - 当前子树完成后，如果存在兄弟节点，继续处理兄弟节点。

- `return` 决定是否回到父节点。

    - 当前节点及其兄弟节点都完成后，向父节点回溯。

- 回溯到 root 且没有下一个节点时，Render 阶段完成。

    - root 得到 finishedWork。

    - 后续进入 Commit。

##### child / sibling / return：用链式结构保存遍历路径

组件树：

```Plain Text
App
└── SearchPage
    ├── SearchInput
    └── BigList
```

Fiber 链式关系：

```Plain Text
AppFiber.child = SearchPageFiber

SearchPageFiber.child = SearchInputFiber
SearchInputFiber.sibling = BigListFiber

SearchInputFiber.return = SearchPageFiber
BigListFiber.return = SearchPageFiber
SearchPageFiber.return = AppFiber
```

执行路径：

```Plain Text
AppFiber
  ↓ child
SearchPageFiber
  ↓ child
SearchInputFiber
  ↓ sibling
BigListFiber
  ↓ return
SearchPageFiber
  ↓ return
AppFiber
```

- `child` 保存向下路径。

    - React 能从父节点进入第一个子节点。

- `sibling` 保存横向路径。

    - React 能在同层节点之间继续推进。

- `return` 保存回溯路径。

    - React 能在子树完成后回到父节点。

- 三个指针共同让遍历脱离 JS 调用栈。

    - 暂停时不丢失路径。

    - 恢复时不需要从 root 重新遍历所有节点。

##### 时间分片：降低单次主线程占用时间

时间分片控制的是单次连续执行时长。

旧同步递归：

```Plain Text
Item 1 → Item 2 → ... → Item 10000 → Commit
```

Fiber 分片执行：

```Plain Text
Item 1 → ... → Item 1000
  ↓ 让出主线程
Item 1001 → ... → Item 2500
  ↓ 让出主线程
Item 2501 → ... → Item 10000
  ↓
Commit
```

- 总计算量仍然存在。

    - Fiber 不是减少所有计算量，而是拆短连续阻塞时间。

- 单次主线程占用变短。

    - 浏览器可以在时间片之间处理输入、事件和绘制。

- 用户感知变好。

    - 页面从“长时间无响应”变成“后台逐步完成”。

#### 模块实现例子

假设 React 处理到 `Item3000Fiber` 时需要让出主线程：

```Plain Text
nextUnitOfWork = Item3001Fiber

workInProgress tree
SearchPage('a', 'a')
├── SearchInput('a') flags: Update
└── BigList('a')
    ├── Item1 已处理
    ├── ...
    ├── Item3000 已处理
    └── Item3001 待处理
```

此时真实 DOM 尚未修改，但 workInProgress tree 已经保存了中间计算结果，`nextUnitOfWork` 保存了恢复位置。

这一层的本质是：React 用 Fiber 链式结构和工作循环，把同步递归改造成可暂停、可恢复、可分片推进的任务流。

---

### 3\.3 双缓存与阶段隔离：用 workInProgress 计算未来 UI，用 current 保持当前 UI

**从直接覆盖到内存中试算：** 可中断 Render 会产生中间状态：下一版 UI 可能只算了一部分，或者算完后又被更高优先级更新打断。React 不能让这些未完成结果污染当前屏幕。当前 UI 必须保持稳定，下一版 UI 又必须允许暂停、恢复、重做和丢弃。因此 React 将“已经提交到屏幕的版本”保存在 current tree，将“正在计算的下一版”保存在 workInProgress tree。Render 的计算结果先写入 workInProgress，只有整棵树完成并进入 Commit 后，才切换成新的 current。

#### 核心机制

##### current tree：屏幕已确认版本

current tree 表示用户当前看到的 UI。

```Plain Text
current tree
SearchPage(keyword: '', listKeyword: '')
├── SearchInput(value: '')
└── BigList(keyword: '')
```

- current Fiber 保存上一次提交后的 props、state、DOM 引用。

    - 用户当前看到的 DOM 与 current tree 对应。

    - 事件触发时，React 以 current tree 作为已确认基础。

- Render 中间结果不会覆盖 current。

    - workInProgress 没有完成前，current 继续保持稳定。

    - 未提交结果被丢弃时，不影响屏幕上的 UI。

##### workInProgress tree：内存中的下一版 UI

更新开始后，React 基于 current tree 创建 workInProgress tree。

```Plain Text
current tree                         workInProgress tree
SearchPage('', '')      alternate    SearchPage(计算中)
├── SearchInput('')                  ├── SearchInput(计算中)
└── BigList('')                      └── BigList(计算中)
```

- workInProgress tree 承载本轮更新的计算结果。

    - `pendingProps`、`memoizedState`、`flags` 会在这棵树上更新。

- workInProgress 可以暂停。

    - 已完成的 Fiber 结果保留在树上。

    - 未完成的位置由 `nextUnitOfWork` 保存。

- workInProgress 可以重做。

    - 更高优先级更新到来时，低优先级中间结果可以被丢弃或重新计算。

- Render 完整结束后，workInProgress 成为 `finishedWork`。

    - 它代表下一版 UI 已经计算完整，可以进入 Commit。

##### alternate：两棵树之间的复用通道

```JavaScript
function createWorkInProgress(current, pendingProps) {
  let wip = current.alternate;

  if (wip === null) {
    wip = new Fiber();
    wip.alternate = current;
    current.alternate = wip;
  }

  wip.pendingProps = pendingProps;
  wip.memoizedProps = current.memoizedProps;
  wip.memoizedState = current.memoizedState;
  wip.updateQueue = current.updateQueue;

  wip.flags = NoFlags;
  wip.subtreeFlags = NoFlags;
  wip.deletions = null;

  return wip;
}
```

- 首次更新时创建 alternate Fiber。

    - current 和 workInProgress 建立双向引用。

- 后续更新时复用 alternate。

    - 减少 Fiber 对象重复创建。

    - 复用上轮已经存在的结构。

- current 提供上轮稳定结果。

    - `memoizedProps`、`memoizedState`、`updateQueue` 可以作为本轮计算基础。

- workInProgress 写入本轮计算结果。

    - `flags`、`subtreeFlags`、`deletions` 需要重置并重新收集。

##### finishedWork：Render 完成后的提交对象

当 workInProgress tree 完整计算结束后，root 会持有 `finishedWork`。

```Plain Text
root.finishedWork = workInProgress tree
```

- `finishedWork` 表示下一版 UI 已经计算完整。

    - 所有需要处理的 Fiber 已经完成 beginWork 和 completeWork。

- `finishedWork` 上已经收集副作用。

    - 插入、删除、更新等计划已经写入 flags。

- `finishedWork` 是 Commit 阶段的输入。

    - Commit 不重新计算 UI。

    - Commit 只消费 Render 阶段生成的提交计划。

##### Render / Commit 阶段边界：计算与提交分离

Render 阶段：

```Plain Text
读取 updateQueue
计算新 state
生成子 Fiber
标记 flags
允许暂停、恢复、重做
```

- Render 修改的是内存中的 Fiber。

    - 不直接修改真实 DOM。

- Render 可以被打断。

    - 未完成结果可以保留或丢弃。

- Render 可以按优先级重算。

    - 高优先级任务可以插队。

Commit 阶段：

```Plain Text
执行 DOM 插入、删除、更新
执行 ref 处理
执行 layout effect
切换 root.current
同步完成
```

- Commit 修改真实 DOM。

    - 它对应用户能直接看到的界面变化。

- Commit 必须同步完成。

    - 避免 DOM 只提交一半导致 UI 不一致。

- Commit 完成后，finishedWork 成为新的 current tree。

    - 下一轮更新再以它为已确认基础。

#### 模块实现例子

如果用户输入 `a` 后，BigList 的 Transition 渲染处理到一半，此时 workInProgress 可能已经包含部分 `BigList('a')` 的结果；但 current tree 仍然是上一版 UI。

```Plain Text
current tree
SearchPage(keyword: '', listKeyword: '')
├── SearchInput(value: '')
└── BigList(keyword: '')

workInProgress tree
SearchPage(keyword: 'a', listKeyword: 'a')
├── SearchInput(value: 'a') flags: Update
└── BigList(keyword: 'a')
    ├── Item1 已处理
    ├── ...
    └── Item3001 待处理
```

如果此时更高优先级的输入 `ab` 到来，未提交的 `BigList('a')` 可以被丢弃或重算，屏幕不会出现半成品 UI。

这一层的本质是：React 在 workInProgress tree 中计算未来 UI，再把完整结果一次性切换成当前 UI。

---

### 3\.4 Lane 调度与优先级：让紧急更新先完成，让低优先级更新可让步

**从单一更新队列到优先级通道：** Fiber 和工作循环解决了“能不能暂停”的问题，但还需要解决“暂停后先处理什么”的问题。输入回显、点击反馈、大列表过滤、空闲预渲染的紧急程度不同，不能全部按同一优先级执行。React 需要把更新的紧急程度写入内部数据流，让 root 能看到整棵树里有哪些待处理任务，并选择最值得优先完成的一批。Lane 因此被设计成优先级集合：一次更新进入 React 后会被分配 lane，lane 写入当前 Fiber，并沿父链冒泡到 root。高优先级更新可以先完成，低优先级任务继续保留，后续再分片处理或基于最新状态重算。

#### 核心机制

##### Update：状态变化的内部记录

一次 `setState` 会创建 update。

```TypeScript
type Update = {
  lane: Lane;
  payload: any;
  next: Update | null;
};
```

update 会进入对应 Fiber 的 `updateQueue`：

```Plain Text
SearchPageFiber.updateQueue
  ├── update(payload: keyword = 'a', lane: SyncLane)
  └── update(payload: listKeyword = 'a', lane: TransitionLane)
```

- `payload` 表示状态变化内容。

    - 例如输入框的 `keyword = 'a'`。

    - 例如列表过滤条件的 `listKeyword = 'a'`。

- `lane` 表示这次更新的优先级。

    - SyncLane 可以优先参与本轮 Render。

    - TransitionLane 可以延后处理。

- `next` 串联多个 update。

    - 多次输入可能形成多个 update。

    - React 根据当前 render lanes 选择要处理的 update。

##### Lane：用位掩码表达优先级集合

Lane 可以理解成更新通道。

```Plain Text
SyncLane              输入、点击等高优先级更新
InputContinuousLane   拖拽、滚动等连续输入更新
DefaultLane           默认状态更新
TransitionLane        startTransition 标记的过渡更新
IdleLane              空闲任务
```

- Lane 用位掩码表示。

    - 一个 root 可以同时存在多个 lanes。

    - React 可以通过位运算合并、筛选和判断优先级。

- 高优先级 lane 先进入 Render。

    - 输入、点击等用户敏感任务优先完成。

- 低优先级 lane 保留。

    - 大列表、过渡 UI、非紧急任务可以后续处理。

一个 root 上可以同时存在多个 lanes：

```Plain Text
root.pendingLanes = SyncLane | TransitionLane
```

##### Lane 冒泡：让 root 感知整棵树的任务

更新发生在某个组件 Fiber 上，但调度入口在 root。

```Plain Text
SearchPageFiber.lanes |= SyncLane
AppFiber.childLanes |= SyncLane
RootFiber.childLanes |= SyncLane
root.pendingLanes |= SyncLane
```

- 当前 Fiber 记录自身更新。

    - `SearchPageFiber.lanes` 表示 SearchPage 自己有更新。

- 父 Fiber 记录子树更新。

    - `AppFiber.childLanes` 表示 App 子树里有更新。

- root 记录整棵树待处理 lanes。

    - 调度器从 root 统一选择下一批任务。

- 冒泡路径让局部更新变成全局可调度任务。

    - React 不需要盲目扫描整棵树才能知道哪里有任务。

##### 子树跳过：用 childLanes 减少无效遍历

`childLanes` 让 React 判断某棵子树在当前优先级下是否需要处理。

```Plain Text
当前 Render lanes = SyncLane

BigListFiber.childLanes = TransitionLane
```

- 当前 Render 只处理 SyncLane。

    - 输入框更新需要优先完成。

- BigList 子树只有 TransitionLane。

    - 本轮 Sync 渲染可以跳过 BigList。

- 被跳过的低优先级任务不会丢失。

    - TransitionLane 仍然保留在 root\.pendingLanes 中。

    - 后续调度继续处理。

结果是：

- 输入框更新快速完成。

- 大列表更新继续保留。

- 用户先看到输入响应，再等待列表过渡更新。

##### Transition：把大渲染标记为可延后更新

搜索输入场景：

```TypeScript
function SearchPage() {
  const [keyword, setKeyword] = useState('');
  const [listKeyword, setListKeyword] = useState('');
  const [isPending, startTransition] = useTransition();

  function handleInput(e) {
    const value = e.target.value;

    setKeyword(value);

    startTransition(() => {
      setListKeyword(value);
    });
  }

  return (
    <>
      <input value={keyword} onChange={handleInput} />
      {isPending && <span>列表更新中...</span>}
      <BigList keyword={listKeyword} />
    </>
  );
}
```

内部语义：

```Plain Text
setKeyword(value)
  → 高优先级 lane
  → 输入框尽快响应

startTransition(setListKeyword(value))
  → TransitionLane
  → BigList 可延后、可中断、可重做
```

- `setKeyword` 负责输入框受控值。

    - 用户对延迟极敏感。

    - 应该优先提交。

- `setListKeyword` 负责大列表过滤条件。

    - 计算量大。

    - 可以延后，不应该阻塞输入。

- `isPending` 表示低优先级更新尚未完成。

    - 用户可以看到列表仍在更新中。

    - 输入交互不被大列表渲染拖住。

#### 模块实现例子

用户输入 `a` 时，React 可以把输入框更新和大列表更新拆成两条优先级不同的任务：

```Plain Text
setKeyword('a')
  → SyncLane
  → 本轮优先完成 input value = 'a'

setListKeyword('a')
  → TransitionLane
  → 后续分片处理 BigList('a')
```

如果输入 `a` 的列表渲染还没完成，用户又输入 `ab`，新的 `SyncLane` 会插队，React 优先完成 `input value = 'ab'`，再决定是否重做 BigList 的 Transition 渲染。

这一层的本质是：Lane 把“更新紧急程度”写进 React 内部数据流，让 Render 按用户感知价值排序。

---

### 3\.5 副作用标记与集中提交：Render 生成变更计划，Commit 执行真实修改

**从边计算边修改到先计划后提交：** Render 阶段可以暂停、恢复和重做，因此它不能边算边直接修改真实 DOM。真实 DOM 是用户当前看到的界面，必须在完整结果形成后统一修改，避免出现半成品状态。React 把插入、删除、属性更新、ref 处理、effect 处理记录为 Fiber 上的副作用标记；等 workInProgress tree 完整计算成 finishedWork 后，Commit 阶段再按固定顺序消费这些标记。这样 Render 保持可调度，Commit 保持 UI 一致性。

#### 核心机制

##### flags：记录当前 Fiber 的变更类型

常见副作用可以简化成：

```JavaScript
const NoFlags = 0b0000;
const Placement = 0b0001;
const Update = 0b0010;
const Deletion = 0b0100;
const Ref = 0b1000;
```

- `Placement` 表示需要插入 DOM。

    - 新 Fiber 对应的 DOM 节点需要在 Commit 阶段挂载。

- `Update` 表示需要更新 DOM。

    - 属性、文本、事件等发生变化时会打上该标记。

- `Deletion` 表示需要删除 DOM。

    - 旧 Fiber 无法复用时，会进入删除流程。

- `Ref` 表示需要处理 ref。

    - ref 解绑和绑定需要在 Commit 的特定阶段执行。

- flags 只描述计划，不直接执行修改。

    - Render 阶段负责记录。

    - Commit 阶段负责消费。

##### completeWork：为当前节点生成提交计划

```JavaScript
function completeWork(fiber) {
  if (fiberNeedsInsert(fiber)) {
    fiber.flags |= Placement;
  }

  if (fiberNeedsUpdate(fiber)) {
    fiber.flags |= Update;
  }

  if (fiberNeedsDelete(fiber)) {
    fiber.flags |= Deletion;
  }

  bubbleProperties(fiber);
}
```

- 对 HostComponent 准备 DOM 属性更新。

    - 例如 className、style、事件监听等变化。

- 对 HostText 准备文本更新。

    - 文本内容变化时标记 Update。

- 对新节点标记 Placement。

    - Commit 阶段再执行真实插入。

- 对删除节点记录 deletions。

    - 删除通常需要父 Fiber 记录要删除的子节点。

- 向父节点汇总子树副作用。

    - 父节点通过 `subtreeFlags` 感知子树是否有提交任务。

##### subtreeFlags：把子树副作用向上冒泡

```JavaScript
function bubbleProperties(fiber) {
  let subtreeFlags = NoFlags;
  let child = fiber.child;

  while (child !== null) {
    subtreeFlags |= child.subtreeFlags;
    subtreeFlags |= child.flags;
    child = child.sibling;
  }

  fiber.subtreeFlags |= subtreeFlags;
}
```

- 子 Fiber 的 flags 会汇总到父 Fiber。

    - 父节点知道子树里存在副作用。

- 父 Fiber 的 subtreeFlags 会继续向上冒泡。

    - root 最终拿到整棵树的提交计划摘要。

- Commit 阶段可以跳过无副作用子树。

    - 如果某个子树没有 flags，也没有 subtreeFlags，就不需要深入遍历提交。

- 副作用计划从叶子节点向根节点聚合。

    - Render 结束时，finishedWork 已经带有完整提交信息。

##### commitRoot：按阶段执行提交计划

```JavaScript
function commitRoot(root) {
  const finishedWork = root.finishedWork;

  commitBeforeMutationEffects(finishedWork);
  commitMutationEffects(finishedWork);

  root.current = finishedWork;

  commitLayoutEffects(finishedWork);
  schedulePassiveEffects(finishedWork);
}
```

- Before Mutation 阶段在 DOM 修改前执行。

    - 读取必要快照。

    - 处理部分生命周期前置逻辑。

- Mutation 阶段执行真实 DOM 修改。

    - 插入 DOM。

    - 删除 DOM。

    - 更新属性和文本。

    - 处理 ref 解绑。

- Current 切换阶段确认新树。

    - `root.current = finishedWork`。

    - workInProgress tree 成为新的 current tree。

- Layout Effects 阶段处理布局相关副作用。

    - 执行 `useLayoutEffect`。

    - 执行需要在绘制前完成的逻辑。

    - 处理 ref 绑定。

- Passive Effects 阶段调度普通副作用。

    - `useEffect` 不阻塞本次 DOM 提交。

    - 它会在提交后的异步阶段执行。

#### 模块实现例子

如果搜索结果列表中有新增、复用和删除的 Item，Render 阶段不会直接操作 DOM，而是生成提交计划：

```Plain Text
BigListFiber
  subtreeFlags: Placement | Update | Deletion

Item1Fiber
  flags: Update

Item2Fiber
  flags: Placement

Item3Fiber
  flags: Deletion
```

Commit 阶段再统一执行：

```Plain Text
删除失效 DOM
插入新增 DOM
更新复用 DOM
切换 root.current
执行 layout effect
调度 passive effect
```

这一层的本质是：React 把 Render 阶段产出的分散变更，整理成 Commit 阶段的一次性提交计划。

---

### 3\.6 完整例子：搜索框输入 a 后快速输入 ab

这个例子把 Fiber 工作单元、工作循环、双缓存、Lane、时间分片、副作用标记和 Commit 串成一条完整链路。

组件结构：

```Plain Text
App
└── SearchPage
    ├── SearchInput
    └── BigList
        ├── Item 1
        ├── Item 2
        ├── ...
        └── Item 10000
```

代码场景：

```TypeScript
function SearchPage() {
  const [keyword, setKeyword] = useState('');
  const [listKeyword, setListKeyword] = useState('');
  const [isPending, startTransition] = useTransition();

  function handleInput(e) {
    const value = e.target.value;

    setKeyword(value);

    startTransition(() => {
      setListKeyword(value);
    });
  }

  return (
    <>
      <input value={keyword} onChange={handleInput} />
      {isPending && <span>列表更新中...</span>}
      <BigList keyword={listKeyword} />
    </>
  );
}
```

#### 第一步：输入 a 后创建 update

用户输入 `a` 后，React 创建两类 update：

```Plain Text
setKeyword('a')
  → payload: keyword = 'a'
  → lane: SyncLane

setListKeyword('a')
  → payload: listKeyword = 'a'
  → lane: TransitionLane
```

它们进入 `SearchPageFiber.updateQueue`：

```Plain Text
SearchPageFiber.updateQueue
  ├── update(keyword = 'a', lane = SyncLane)
  └── update(listKeyword = 'a', lane = TransitionLane)
```

lane 向上冒泡：

```Plain Text
SearchPageFiber.lanes |= SyncLane | TransitionLane
AppFiber.childLanes |= SyncLane | TransitionLane
RootFiber.childLanes |= SyncLane | TransitionLane
root.pendingLanes |= SyncLane | TransitionLane
```

此时 root 已经知道：输入框有紧急更新，大列表有过渡更新。

#### 第二步：创建 workInProgress tree

当前屏幕仍然对应 current tree：

```Plain Text
current tree
SearchPage(keyword: '', listKeyword: '')
├── SearchInput(value: '')
└── BigList(keyword: '')
```

React 创建 workInProgress tree：

```Plain Text
current tree                         workInProgress tree
SearchPage('', '')      alternate    SearchPage(计算中)
├── SearchInput('')                  ├── SearchInput(计算中)
└── BigList('')                      └── BigList(计算中)
```

这个阶段的关键状态：

- current tree 保持屏幕稳定。

- workInProgress tree 承载本轮计算。

- updateQueue 被复制或复用到 workInProgress Fiber。

- flags、subtreeFlags 被重置，等待本轮重新收集。

#### 第三步：workLoop 从 root 开始逐个处理 Fiber

React 进入工作循环：

```Plain Text
nextUnitOfWork = RootFiber
```

执行顺序大致是：

```Plain Text
RootFiber
  ↓
AppFiber
  ↓
SearchPageFiber
  ↓
SearchInputFiber
  ↓
BigListFiber
  ↓
Item1Fiber
  ↓
Item2Fiber
  ↓
...
```

处理 `SearchPageFiber`：

```Plain Text
beginWork(SearchPageFiber)
  ↓
读取 updateQueue
  ↓
计算 keyword = 'a'
  ↓
计算 listKeyword = 'a'
  ↓
生成 SearchInput 和 BigList 的子 Fiber
```

处理 `SearchInputFiber`：

```Plain Text
beginWork(SearchInputFiber)
  ↓
发现 value 从 '' 变成 'a'

completeWork(SearchInputFiber)
  ↓
SearchInputFiber.flags |= Update
```

处理 `BigListFiber`：

```Plain Text
beginWork(BigListFiber)
  ↓
根据 listKeyword = 'a' 生成 10000 个 Item Fiber
  ↓
继续进入 Item 子树
```

#### 第四步：时间片用完后暂停 Render

假设 React 处理到 `Item3000Fiber` 时，`shouldYield()` 返回 true。

暂停时内部状态可以理解为：

```Plain Text
nextUnitOfWork = Item3001Fiber

workInProgress tree
SearchPage('a', 'a')
├── SearchInput('a') flags: Update
└── BigList('a')
    ├── Item1 已处理
    ├── ...
    ├── Item3000 已处理
    └── Item3001 待处理
```

此时：

- DOM 尚未修改。

- current tree 仍然稳定。

- 已处理结果保存在 workInProgress tree。

- 下一个处理位置保存在 `nextUnitOfWork`。

- 后续调度恢复时可以从 `Item3001Fiber` 继续。

#### 第五步：输入 ab 后高优先级更新插队

用户继续输入 `b`，触发新的更新：

```Plain Text
setKeyword('ab')
  → lane: SyncLane

setListKeyword('ab')
  → lane: TransitionLane
```

新的 update 进入队列：

```Plain Text
SearchPageFiber.updateQueue
  ├── update(keyword = 'a', lane = SyncLane)
  ├── update(listKeyword = 'a', lane = TransitionLane)
  ├── update(keyword = 'ab', lane = SyncLane)
  └── update(listKeyword = 'ab', lane = TransitionLane)
```

调度器看到新的 `SyncLane`：

```Plain Text
当前未完成任务：TransitionLane 渲染 BigList('a')
新进入任务：SyncLane 更新 input('ab')
```

执行选择：

```Plain Text
优先处理 SyncLane
  ↓
完成 input value = 'ab'
  ↓
未提交的 BigList('a') 中间结果保留或丢弃
  ↓
后续基于 listKeyword = 'ab' 重新计算 BigList
```

这个过程的关键点：

- `BigList('a')` 的 Render 结果停留在 workInProgress tree。

- 未进入 Commit 的结果可以被重做。

- current tree 没有被中途污染。

- 用户输入 `ab` 可以优先响应。

#### 第六步：先提交输入框，保证用户感知优先

React 可以先完成高优先级输入更新：

```Plain Text
Commit 1
SearchInput(value: 'ab')
BigList 维持上一版已提交 UI
isPending 显示列表更新中
```

用户感知结果：

- 输入框立即显示 `ab`。

- 大列表稍后更新。

- 页面主线程没有被一次大列表 Render 长时间占满。

内部结果：

```Plain Text
root.current
SearchPage(keyword: 'ab', listKeyword: 旧值或待更新状态)
├── SearchInput(value: 'ab')
└── BigList(上一版已提交列表)
```

#### 第七步：继续渲染列表，TransitionLane 分片完成

React 后续处理 `listKeyword = 'ab'` 的 TransitionLane 更新。

```Plain Text
Render BigList('ab')
  ↓
处理 Item1 ~ Item1000
  ↓
shouldYield，暂停
  ↓
恢复
  ↓
处理 Item1001 ~ Item3000
  ↓
继续分片
  ↓
完成 Item10000
```

Render 完成后，finishedWork 上已经有完整提交计划：

```Plain Text
SearchPageFiber subtreeFlags: Update | Placement | Deletion

SearchInputFiber
  flags: Update

BigListFiber
  subtreeFlags: Placement | Update | Deletion

部分 ItemFiber
  flags: Placement / Update / Deletion
```

#### 第八步：最终 Commit，集中修改 DOM 并切换 current

React 进入 Commit：

```Plain Text
commitBeforeMutationEffects
  ↓
commitMutationEffects
  ↓
root.current = finishedWork
  ↓
commitLayoutEffects
  ↓
schedulePassiveEffects
```

真实 DOM 修改集中发生：

- 更新 input value。

- 插入新的列表项。

- 删除失效列表项。

- 更新复用列表项的文本或属性。

- 处理 ref。

- 执行 layout effect。

- 调度 passive effect。

提交完成后：

```Plain Text
current tree
SearchPage(keyword: 'ab', listKeyword: 'ab')
├── SearchInput(value: 'ab')
└── BigList(keyword: 'ab')
    ├── Item 1
    ├── Item 2
    ├── ...
    └── Item 10000
```

---

### 3\.7 新旧架构对比

- **旧 Stack Reconciler：** React 已经有 Reconciliation / Diff 和更新链路，但 Render / Reconciliation 主要依赖同步递归执行；进度依赖 JS 调用栈；大树更新会形成长任务；输入响应、事件回调和绘制机会会被延后。

- **Fiber 架构：** 每个节点变成 Fiber 工作单元；更新进入 `updateQueue`；优先级写入 `lanes`；遍历路径由 `child / sibling / return` 保存；执行由 `workLoop` 推进；中间结果写入 workInProgress tree；变化计划记录在 `flags`；最终由 Commit 集中提交。

- **关键差异：** Fiber 改造的是 Reconciliation 的执行架构，不是让 React 才拥有 Diff。它把同步递归执行升级为可保存进度、可分片推进、可优先级调度、可丢弃未提交结果、可集中提交的任务系统。

## 是

