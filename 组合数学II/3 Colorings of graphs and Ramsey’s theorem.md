
# Chromatic Number

> [!definition]
> A proper coloring of a graph $G$ is a function from the vertices to a set $C$ of 'colors' (e.g. $C=\{1,2,3,4\}$) such that the ends of every edge have distinct colors.
> If $|C|=k$, we say that $G$ is $k$-colored.
> 
> The chromatic number $\chi(G)$ of a graph $G$ is the minimal number of colors for which a proper coloring exists.

If $\chi(G)=2$, then $G$ is called bipartite. 
A graph with no odd polygons (equivalently, no closed paths of odd length) is bipartite as the reader should verify.

> [!theorem] Brooks
> Let $d \geqslant 3$ and let $G$ be a graph in which all vertices have degree $\leqslant d$ and such that $K_{d+1}$ is not a subgraph of $G$. Then $\chi(G) \leqslant d$.

`\begin{proof}`
See [[A course in combinatorics - 1992 - van Lint, Wilson.pdf]], page 24. 
`\end{proof}`


# Ramsey Theory on Graphs

> [!problem]
> Can we have a party with $6$ people such that no $3$ know each other and no $3$ do not know each other?

> [!definition]
> Define $R(s,t)$ as the smallest integer $n$ such that all (edge)-colorings with $2$ colors $\{c_1,c_2\}$ of $K_n$ contain a monochromatic $K_s$ in color $c_1$ or a monochromatic $K_t$ in color $c_2$. 
> It also equals the smallest integer $n$ such that all graphs $G$ on $n$ vertices satisfy
> - $K_s$ is a subgraph of $G$;
> - $K_t$ is a subgraph of $\overline G$. 

For example, $R(3,3)=6$, $R(2,t)=R(t,2)=t$.

> [!proposition]
> $R(s,t)\leqslant R(s-1,t)+R(s,t-1)$. ^b25753

`\begin{proof}`
Consider a graph $G$ on $n$ vertices without $K_s$ in $G$ and without $K_t$ in $\overline G$. 
Let $x$ be a vertex. 
Then $N(x)$ cannot contain any $K_{s-1}$ and so $|N(x)|\leqslant R(s-1,t)-1$. 
Also $\overline{N}(x)$ cannot contain any $K_{t-1}$ and so $|\overline N(x)|\leqslant R(s,t-1)-1$. 

Hence $R(s,t)-1\leqslant |\{x\}|+|N(x)|+|\overline N(x)|\leqslant 1+R(s-1,t)-1+R(s,t-1)-1$. 
Now we finish the proof. 
`\end{proof}`


> [!corollary]
> $R(r,s)\leqslant {{r+s-2}\choose {r-1}}$.  ^bxbn9o

`\begin{proof}`
Note that $R(1,s)=R(r,1)=1$. 
Then by [[#^b25753]] and by induction. 
`\end{proof}`


> [!definition]
> Define $R(r;m):=R(r_1,\cdots,r_m)$ with $r=r_1=\cdots=r_m$ for $m$ colors. 

## Diagonal Ramsey Numbers

> [!theorem]
> $C\cdot 2^{s/2}\leqslant R(s,s)\leqslant D\cdot 4^{s-1}$. 
> - $C$: Erdos, 1947
> - $D$: Erdos, Szekeres, 1935

**Remark.**
In 2024, $R(s,s)\leqslant (4-\epsilon)^s$, see [here](https://arxiv.org/abs/2303.09521). 
In 2025, an improvement lower bound of $R(s,cs)$, see [here](https://arxiv.org/pdf/2507.12926). 

`\begin{proof}`
By [[#^bxbn9o]] and Stirling's formula,

$$
R(s,s)\leqslant {2s-2 \choose s-1}=\frac{(2s-2)!}{((s-1)!)^2}
$$ 
we finish the proof of upper bound. 

For the lower bound, consider a $K_n$. 
There are $2^{\binom{n}{2}}$ different ways of coloring the edges red or blue. 
Now fix a subgraph $K_p$. 
There are $2^{\binom{n}{2}-\binom{p}{2}+1}$ colorings for which that $K_p$ is monochromatic. 

The number of colorings for which some $K_p$ is monochromatic is at most $\binom{n}{p}$ times as large (because we may count some colorings more than once). 
If this number is less than the total number of colorings, then there exist colorings with no monochromatic $K_p$. 
Using the fact that $\binom{n}{p}<n^p / p!$, we find that such a coloring certainly exists if $n<2^{p / 2}$ (unless $p=2$ ). 

This proves the following theorem.
`\end{proof}`

## Off-diagonal Ramsey Numbers

Reference table for off-diagonal Ramsey bounds (compiled by lyh).

![[Pasted image 20260311140134.png|700]]


# Ramsey Theory on Structures and Spaces

> [!theorem] Schur's theorem
> Let $n$ be a positive integer, and let $s_n$ be the smallest integer such that $[s_n]$ colored in $n$ colors has monochromatic $x+y=z$. 
Such $s_n$ exists. 

`\begin{proof}`
We identify that $n$ colors with $[n]$. 
Define a coloring $K_{s_n}$ with $V(K_{s_n})=[n]$ with $uv$ in color $x\in [n]$ if $|u-v|$ has color $x$. 

If $s_n\geqslant R(3,\cdots,3)=R(n;3)$, then we find a monochromatic $K_{3}$. 
That is, $|v-u|$, $|v-w|$, $|u-w|$ is monochromatic. 
WLOG assume $u>v>w$ and put $x=u-v$, $y=v-w$ and $z=u-w$. 
Then $x+y=z$.
`\end{proof}`


> [!definition]
> Define $[q]^n:=\{(x_1,\cdots,x_n):x_i\in [q]\}$. We say $L\subseteq[q]^n$ is a *combinatorial line* if there exists $I\subseteq [n]$ and integers $a_i$ such that 
> 
> $$
> L=\{(x_1,\cdots,x_n)\in [q]^n:x_i=a_i\text{ for }i\notin I\text{ and }x_i=x_j\text{ for all }i,j\in I\}.
> $$ 

> [!theorem] Hales-Jewett
> For all $r,q\in \mathbb{N}_+$, there exists smallest $n:=HJ(r,q)$ such that any $r$-coloring of $[q]^n$ contains a monochromatic combinatorial line. 

`\begin{proof}`
By induction on $q$. 
The case of $q=1$ is trivial, and we now assume that $q\geqslant 2$. 

For a line $L$, we write $L^{-}$ for its first point and $L^+$ for its last point. 
We call $L_1,\cdots,L_s$ *focused at* $f$ if $L^+=f$ for all $i\in [s]$. 
We call $L_1,\cdots,L_s$ *color-focused* at $f$ if all the truncated lines are monochromatic and of pairwise different colors. 
Note that a line is determined by one point and a "direction". 

Suppose that $HJ(r,q')$ is finite for all $q'\leqslant q-1$. 
Our goal is, for each $s\leqslant r$, show there exists $N=FHJ(r,s,q)$ such that any $r$-coloring of $[q]^N$ either
- contains a monochromatic combinatorial line, or
- contains $s$ color-focused lines. 

Then $r=s$ will show the Hales-Jewett theorem by the pigeonhole principle.

Now we prove our goal by induction on $s$:
When $s=1$, pick $FHJ(r,1,q)=HJ(r,q-1)$. 
Now suppose that $FHJ(r,s',q)$ is finite for all $s'\leqslant s-1$. 
We claim that 

$$
FHJ(r,s,q)\leqslant N=FHJ(r,s-1,q)+HJ(r^{q^n},q-1)=:n+n'.
$$

Suppose $x$ is $r$-coloring $[q]^N$, where $[q]^N=\{(a_1,\cdots,a_{n'},\cdots,a_N):a_i\in [q]\}$.
Then we can write $(a_1,\cdots,a_{n},\cdots,a_N)$ as $(a,b)$, where $a=(a_1,\cdots,a_n)$ and $b=(a_{n+1},\cdots,a_N)$. 
So $x$ can be identified as an $r^{q^n}$-coloring $[q]^{n'}$, by associating each point $b\in [q]^{n'}$ with the entire $r$-colored cube $\{(a,b):a\in [q]^n\}$. 
For each $b\in [q]^{n'}$, its color in $x'$ is $x'(b)$, which is indeed a function $f_b:[q]^n\to [r],a\mapsto x(a,b)$. 

Since $n'=HJ(r^{q^n},q-1)$, there exists a line $L$ with coordinate set $I'$ such that $L\setminus\{L^+\}$ is monochromatic under $x'$. 
For any $b,b'\in L\setminus \{L^+\}$, we have $x'(b)=x'(b')$, i.e. $f_b=f_{b'}$ for all $a\in [q^n]$. 
Define $x''(a):=x((a,b))=x((a,b'))$ for all $a\in [q]^n$, then we get a $r$-coloring $x''$ on $[q]^n$. 

Since $n=FHJ(r,s-1,q)$, either $[q]^n$ under $x''$ contains a monochromatic combinatorial line, or it contains $s-1$ color focused lines.
If the former holds, then we already get a monochromatic combinatorial line in $[q]^N$ under $x$ and we have done. 
We now assume the latter holds, that is, there exists $s-1$ lines $L_1,\cdots,L_{s-1}$ in $[q]^n$ which are color-focused at $f$. 
Then define $L_1',\cdots,L_s'$ as follows:
- for $1\leqslant i\leqslant s-1$, define $L_i'$ in $[q]^N$ with first point $(L_i^-,L^-)$ and active coordinates $I_i\cup I'$,
- for $i=s$, define $L_s'$ with first point $(f,L^-)$ and active coordinates $I'$,

where
- $I_i \subseteq\{1, \ldots, n\}$ is the set of active coordinates for the line $L_i$ in the subspace $[q]^n$, that is, for any $j \in I_i$, the $j$-th coordinate of points in $L_i$ varies synchronously from 1 to $q$,
- $I^{\prime} \subseteq\left\{n+1, \ldots, n+n^{\prime}\right\}$ is the set of active coordinates for the line $L$ in the subspace $[q]^{n^{\prime}}$. 

 It is easy to check that these lines $L_i'$ are color-focused with focus $(f,L^+)$. 
 Now we finish the proof. 
 `\end{proof}`


