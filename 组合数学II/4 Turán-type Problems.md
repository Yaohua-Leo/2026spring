
> [!definition]
> Let $n$ be an integer, and let $H$ be a graph. The Turan number $ex(n,H)$ denotes the maximal number of edges in an $H$-free on $n$ vertices. Here $H$-free means $H$ is not a subgraph. 
> 
> More generally, define $ex(n,\{H_1,\cdots,H_n\})$ for all $H_i$ forbidden. 

> [!lemma]
> $ex(n,\{C_3,C_4,\cdots,C_n\})=n-1$. 

> [!proposition] Mantel, 1907
> - $ex(n,C_3)=[n^2/4]$ ^v9ka7u

`\begin{proof}`
Let $G=(V,E)$ be $C_3$ free.
Define $n=|V|$ and $m=|E|$. 
For $\{x,y\}\in E$, as $G$ is $C_3$-free, $d(x)+d(y)\leqslant n$. 
By double-counting walks of length $2$, there is 

$$
\sum_{x\in V}d(x)^2=\sum_{\{x,y\}\in E}(d(x)+d(y))\leqslant mn.
$$

By Cauchy-Schwartz and $\sum d(x)=2m$, we find 

$$
mn\geqslant\sum_{x\in V}d(x)^2\geqslant(\sum d(x))^2/n=4m^2/n.
$$

Now we finish the proof. 
`\end{proof}`

`\begin{proof}`
Let $A$ be the largest coclique (i.e., independent set) of $G$. 
As $N(x)$ (i.e. neighborhood of $x$) is edge-less, $|A|\geqslant d(x)$ for all $x\in V$. 
Also, as $A$ largest, $B:=V\setminus A$ meets every edge. 
Hence $\sum_{x\in B}d(x)\geqslant |E|$. 

$|E|\leqslant \sum_{x\in B}d(x)\leqslant |B|\cdot |A|\leqslant(\frac{|A|+|B|}2)^2=n^2/4$.
`\end{proof}`

`\begin{proof}`
For convenience, $|V|=2n$. 
By induction, suppose $|V|=2(n+1)$ and $G:=(V,E)$ is $C_3$-free. 
Take $\{x,y\}\in E$, then by induction hypothesis, the induced subgraph $H$ on $V\setminus\{x,y\}$ has $|E(H)|\leqslant n^2$. 
Note that $d(x)+d(y)\leqslant 2n+2$ and $E(G)\leqslant n^2+2n+1=(n+1)^2$. 
Now we finish the proof. 
`\end{proof}`


> [!theorem] Turan, 1941
> Let $k\geqslant 2$. 
> Then $ex(n,K_{k+1})=[(1-\frac{1}{k})n^2/2]$, and the equality holds if $G=K_{[n/k],\cdots,[n/k]}$. 

`\begin{proof}`
We prove it by induction. 
When $n=1$, trivial. 
When $n=2$, [[#^v9ka7u]]. 
Suppose that it holds for $\leqslant n-1$ vertices. 
Let $G=(V,E)$ with $|V|=n$ and $|E|$ is maximal such that $K_{k+1}$ free. 
By maximality, cliques of size $k$ exists. 
Let $A$ be one of these cliques. 
Put $B=V\setminus A$. 
Then $|E(A)|={k\choose 2}$, and by induction there is $|E(B)|\leqslant (1-1/k)\times(n-k)^2/2={k\choose 2}(\frac{n-k}k)^2$.
Also notices that $|E(A,B)|\leqslant (k-1)(n-k)$.
Therefore,

$$
|E|\leqslant |E(A)|+|E(B)|+|E(A,B)|\leqslant {k\choose 2}+{k\choose 2}\left(\frac{n-k}k\right)^2+(k-1)(n-k)=\left(1-\frac{1}{k}\right)\frac{n^2}{2}.
$$

Now we finish the proof. 
`\end{proof}`

> [!theorem]
> $ex(n,\{C_3,C_4\})\leqslant n\sqrt{n-1}/2$. 

`\begin{proof}`
Define $n=|V(G)|$ and $m=|E(G)|$. 
We count paths $(x,y,z)$, where $x,y,z\in V(G)$. 

Count 1: First pick $x$ and $z$, and there are $n(n-1)$ ways. 
If $x\sim z$, then $0$ choice for $y$; if $x\nsim z$, then at most $1$ choice for $y$. 
Hence number of paths $\leqslant n(n-1)-2m$. 

Count 2: First pick $y$, then $x$ and $z$. 
By Jensen's inequality, we have

$$
n(n-1)-2m\geqslant\#\text{paths}=\sum_{y\in V(G)}\deg(y)(\deg(y)-1)\geqslant n\frac{2m}{n}\left(\frac{2m}{n}-1\right).
$$

It yields that $m\leqslant n\sqrt{n-1}/2$ and we finish the proof.
`\end{proof}`


**Remark.** 
- Equality holds when:
	- $n=2$, $K_2$
	- $m=5$, pentagon
	- $n=10$, [[Petersen Graph|Petersen graph]]
	- $n=50$, Hoffman-Singleton graph
	- $n=3250$, open case
- Asymptotic: $ex(n,\{C_3,C_4\})=(1/2+o(1))n^{1.5}$. Construction uses polarities of projective planes. 
- $ex(n,C_4)\leqslant(\frac{1}{\sqrt 2}+o(1))n^{1.5}$, $ex(n,C_4)\geqslant(\frac{1}{2}+o(1))n^{1.5}$
- Constructions: (here $m$ is the diameter of the corresponding bipartite graph of [[Generalized Polygons|generalized polygon]].)
	- $m=2$, projective planes
	- $m=3$, [[Generalized Quadrangle|generalized quadrangle]]
	- $m=5$, [[Generalized Hexagons|generalized hexagon]]
