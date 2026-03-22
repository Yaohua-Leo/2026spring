
> [!definition]
> A partially ordered set (poset) is a set $P$ together with a binary relation $<$ which is transitive and antisymmetric, i.e.
> - if $x<y$ and $y<z$, then $x<z$;
> - if $x<y$, then not $y<x$.
>   
> Write $x\leqslant y$ if $x<y$ or $x=y$. 
> 
> Elements $x,y\in P$ are comparable if $x\leqslant y$ or $y\leqslant x$. 

> [!definition]
> A chain $C$ is a subset of $P$ such that all its elements are comparable. 

> [!definition]
> An antichain $A$ is a subset of $P$ such that all its elements are not comparable. 


**Questions.**
- How many chains are needed to partition $P$?
- How many antichains are needed to partition $P$?

> [!theorem]
> Suppose that the longest chain in a poset $P$ has size $r$. Then $P$ can be partitioned  into $r$ antichains. 

`\begin{proof}`
Let $A_i$ be the set of $x\in P$ such that the longest chain with $x$ as its longest element has size $i$. 
Then $A_i=\emptyset$ for $i>r$. 
Thus $P=A_1\sqcup\cdots\sqcup A_r$ is a partition of $P$. 
Furthermore, $A_i$ is an antichain. 
`\end{proof}`

> [!theorem] Dilworth's theorem
> Suppose that the longest antichain in a poset has size $r$, then $P$ can be partitioned into $r$ chains.  ^fz5pii

`\begin{proof}`
We do induction on $|P|$. 
It is trivial when $|P|=1$. 

Let $a$ be a largest element in $P$. 
Let $r$ be the size of the longest antichain in $P\setminus\{a\}:=P'$. 
By induction hypothesis, $P'$ is the union of $r$ pairwise disjoint chains $C_1,\cdots,C_r$. 

We aim to show either 
- longest antichain in $P$ has size $r+1$, or
- it is union of $r$ chains. 

Every $r$-element antichain of $P$ contains one element of each $C_i$. 
Let $a_i$ denote the largest element in $c_i$ that belongs to such an antichain. 
Then $A=\{a_1,\cdots,a_r\}$ is an antichain of $P$. 
If $A\cup\{a\}$ is an antichain, then we are done (just add $\{a\}=C_{r+1}$). 
Otherwise $a>a_i$ for some $i$, then 

$$
K=\{a\}\cup\{x\in C_i:x\leqslant a_i\}
$$

is a chain in $P$.

We claim that no $r$-element antichain in $P\setminus K$. 
Otherwise, there exists an antichain $A'$ of length $r$ contained in $P\setminus K$, and there exists $a_i'\in A'$. 
It deduces that $a_i'\leqslant a_i$ and so $a_i'\in K$, leading to a contradiction. 

By induction hypothesis, $P\setminus K$ can be partitioned into $r-1$ chains. 
Now we finish the proof. 
`\end{proof}`


There is another proof of [[5 Hall's Marriage Theorem#^jhp0cl]].

`\begin{proof}`
Suppose that $S_1,\cdots,S_m$ satisfy $|I|\leqslant|S(I)|$ for all $I\subseteq [m]$, where $S(I)=\cup_{i\in I}S_i$. 

Define a post $P$:
- points: element of $\cup_{i=1}^mS_i$ and symbols $y_1,\cdots,y_m$
- $<$: $x<y_i$ if $x\in S_i$. 

Clearly, $X:=\cup_{i=1}^m S_i$ is an antichain of $P$, and this is an longest antichain: Let $A$ be an antichain and put $I:=\{i:y_i\in A\}$. Then $A$ does not contain any point of $S(I)$. 
Hence $|A|\leqslant |I|+|X|-|S(I)|\leqslant |X|$. 

By [[#^fz5pii]], the set $P$ can be partitioned into $|X|$ chains. 
By Pigeonhole principle, there are $m$ chains has length $2$. 

Define $S=\{y_1,\cdots,y_m\}$ and $T=\cup_{i=1}^m S_i$, then the $m$ chains corresponds a maximum matching of $(S\cup T,E)$.
`\end{proof}`


