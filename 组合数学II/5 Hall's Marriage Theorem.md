
> [!definition]
> Let $G=(S\cup T,E)$ be a bipartite graph. 
> A matching $M\subseteq E$ of $G$ is a set of pairwise disjoint edges. 
> 
> Define $m(G)=\max_{M\text{ matching}}|M|$, and we say $M$ is a maximum matching if $|M|=m(G)$. 

**Remark.** Maximal matching may not maximum, just like maximal subgroups of a group have different orders. 

> [!theorem] Hall's Marriage Theorem
> Let $G=(S\cup T,E)$ be a bipartite. 
> Then $m(G)=|S|$ iff $|A|\leqslant |N(A)|$ for all $A\subseteq S$.  ^jhp0cl

`\begin{proof}`
"Only if" is clear. 

Now assume that $|A|\leqslant |N(A)|$ for all $A\subseteq S$. 
Let $M\subseteq E$ be a matching with $|M|<|S|$. 
We will construct a matching $M'$ from $M$ with $|M'|=|M|+1$. 

Let $u_0\in S$ be in no edges of $M$. 
As $|N\{u_0\}|\geqslant |\{u_0\}|=1$, $u_0$ has a neighbor $v_1$. 
If $v_1$ is in no edge of $M$, then $M'=M\cup\{u_0,v_0\}$ and we have done. 
Otherwise $\{u_1,v_1\}\in M$. 
As $|N\{u_1,v_1\}|\geqslant|\{u_1,v_1\}|=2$, we can find a neighbor $v_2$ and replace $(u_1,v_1)$ with $(u_1,v_2)$. 
Repeat this procedure and we have done. 
`\end{proof}`


> [!definition]
> A vertex cover of a graph is a set $W\subseteq V$ such that each edge of $E$ contains at least one vertex of $W$. 

The following proposition is a generalization of [[#^jhp0cl]].

> [!proposition]
> Let $G=(S\cup T,E)$ be a bipartite graph. Then 
> 
> $$
> m(G)=|S|-\max_{A\subseteq S}(|A|-N(A)).
> $$ 
> ^vbxsbz

`\begin{proof}`
Put $\delta:=\max_{A\subseteq S}(|A|-N(A))$, then there exists $A_0\subseteq S$ such that $|A_0|-|N(A_0)|=\delta$. 
Clearly, $\delta$ vertices cannot be matched, so $m(G)\leqslant |S|-\delta$. 

Now we prove that $m(G)\geqslant |S|-\delta$. 
Let $D$ be a set of $\delta$ vertices such that $D\cap (S\cup T)=\emptyset$. 
Put $G^*=(S\cup(T\cup D),E^*)$, where $E^*=E\cup\text{all edges between }S\text{ and }D$. 
Now for all $A\subseteq S$, $N^*(A)=N(A)\cup D$. 
So $|N^*(A)|\geqslant|A|$ and by [[#^jhp0cl]] we find a matching of size $|S|$. 
Throw away all $\leqslant \delta$ edges of the matching using $D$, and we get a matching of $G$ of size $\geqslant |S|-\delta$. 

Now we finish the proof. 
`\end{proof}`


> [!theorem] Kőnig, 1931
> In a bipartite graph $G=(S\cup T,E)$, we have that 
> 
> $$
> \max(|M|:M\text{ matching})=\min(|C|:C\text{ vertex covering}). 
> $$ 
> ^92kx2v

`\begin{proof}`
By [[#^vbxsbz]], $m(G)=|S|-|A_0|+|N(A_0)|=|S\setminus A_0|+|N(A_0)|$ for some $A_0$. 
Note that $N(A_0)\cup (S\setminus A_0)$ is a vertex cover. 
So $\min|C|\leqslant \max|M|$. 

On the other hand, $|C|\geqslant |M|$ for any vertex cover $C$ and any matching $M$, because $C$ must cover each edge of $M$. 
Therefore, $\min|C|=\max|M|$. 
`\end{proof}`

## Transversal Theory

Remark that there is a $1$-$1$ corresponding between bipartite graph and family of sets in $[n]$, where $n=|S|$. 

> [!definition] 
> Let $\mathcal{F}$ be a family of subsets of $[n]$. 
> A transversal of $\mathcal{F}$ is an injective function $\varphi:\mathcal{F}\to[n]$ such that $\varphi(\mathcal{F})\in \mathcal{F}$. 

The following theorem is equivalent to [[#^jhp0cl]]. 

> [!theorem]
> Let $\mathcal{F}=\{F_1,\cdots,F_m\}$ be a family of subsets of $[n]$. 
> Then $\mathcal{F}$ has a transversal iff $|\cup_{i\in I}F_i|\geqslant |I|$ for all $I\subseteq[m]$.  ^w6c21o


> [!theorem] Birkhoff, 1946
> Let $A=(a_{ij})_{n\times n}\in \mathrm{M}_{n\times n}(\mathbb{Z})$ be a matrix with nonnegative entries such that each row/column has sum $\ell$. 
> Then $A$ is the sum of $\ell$ permutation matrices. 

`\begin{proof}`
When $\ell=1$, it is trivial. 
When $\ell> 1$, we prove it by induction. 
Define $\mathcal{F}=\{F_1,\cdots,F_n\}$ by $F_i=\{j:a_{ij}>0\}$. 
For any $k$-tuple in $\mathcal{F}$, the sum of the corresponding rows equals $k\ell$. 
Every column of $A$ has sum $\ell$, so the chosen $k$ rows must have nonzero entries in at least $k$ columns. 
Therefore, for $I$ with $|I|=k$, we have  

$$
|\cup_{i\in I}F_i|\geqslant \#\text{columns have nonzero entries}\geqslant k= |I|.
$$

Hence, by [[#^w6c21o]], there exists a transversal of $\mathcal{F}$. 
That is, there exists a permutation matrix $P=(p_{ij})$ with $p_{ij}=1$ if $a_{ij}>0$. 
Then $A-P$ is a matrix with nonnegative entries such that each row and column has sum $\ell-1$. 
By induction hypothesis, we finish the proof. 
`\end{proof}`

## Max Flow and Min Cut

We can identify a bipartite to a $s$-$t$ flow:
![[Pasted image 20260316195845.png|500]]

> [!theorem] Max-flow min-cut theorem
> The maximum value of an $s$-$t$ flow is equal to the minimum capacity over all $s$-$t$ cuts. ^b9thzu

Remark that maximum flow is the maximum matching, and the minimal cut is the minimal vertex covering. 
So [[#^b9thzu]] is equivalent to [[#^92kx2v]]. 

By reducing it to a flow problem, bipartite matching can be computed efficiently.