
![[Finite Geometry#^lsbefh]]

> [!definition]
> An incidence geometry is a pair $\mathcal{G}=(\Omega,I)$ where $\Omega$ is a set and $I\subseteq \Omega\times \Omega$ is symmetric and transitive. 

> [!definition]
> Let $\mathcal{G}=(\Omega,I)$ be an incidence geometry. 
> A (maximal) flag in $\mathcal{G}$ is a (maximal) chain with $\mathcal{G}$ seen as a poset. 

> [!definition]
> A geometry $\mathcal{G}=(\Omega,I)$ has rank $r$ if we can partition $\Omega$ into $r$ antichains $\Omega_1,\cdots,\Omega_r$. 

> [!definition]
> A projective plane is an incidence geometry of points and lines with the following properties: 
> - Every two points are incident with a unique common line. 
> - Every two lines are incident with a unique common point. 
> - There are four points, no three collinear. 
> 
> Note that i) and ii) are dual, and iii) implies its dual.

> [!proposition]
> - Every point in a finite projective plane is incident with $(n+1)$ lines. 
> - Dually, every line is incident with $(n+1)$ points. 
>   
> $n$ is called the order of the projective plane $\mathcal{G}=(\mathcal{P},\mathcal{L},I)$. 

`\begin{proof}`
There exist a point $P$ and a line $L$ such that $P\not I L$. 
Note that the number of points incident with $L$ equals the number of lines incident with $P$. 
There also exists point $Q$ such that $Q\not IL$, so the number of lines incident with $P$ equals the number of lines incident with $Q$. 

The $P,Q,L$ are arbitrarily chosen, so we finish the proof. 
`\end{proof}`

> [!proposition]
> A finite projective plane of order $n$ has $n^2+n+1$ points and $n^2+n+1$ lines. 

`\begin{proof}`
Each point $x$ has valency $n+1$ and each line incident with $x$ has $n+1$ points including $x$. 
Then $|S|=(n+1)n+1=n^2+n+1$. 
`\end{proof}`



> [!conjecture] Prime Order Conjecture
> For a prime $n$, $PG(2,n)$ is the only projective plane of order $n$. 


> [!conjecture] Prime Power Conjecture
> The order of a projective plane is necessarily a prime power. 

Later we will investigate projective planes in higher dimension. 
There all are $PG(n,q)$, where points are $1$-spaces of $V(n+1,q)$, lines are $2$-spaces and so on. 

> [!theorem] Bruck-Ryser-Chowla
> If there is a projective plane of order $n$ and $n\equiv 1\pmod 4$ of $n\equiv 2\pmod 4$, then $n$ is the sum of two squares. 

`\begin{proof}`
See [[A course in combinatorics - 1992 - van Lint, Wilson.pdf]]. 
`\end{proof}`


**Remark.** For example, a projective plane of order $10$ does not exist, proved by Clement Lam in 1989. Furthermore, the existence of projective plane of order $12$ is still open. 

# One More Construction

> [!definition]
> Let $n$ be a positive integer. A set $\mathcal{D}$ of positive integer is called *difference set* of order $n$ if 
> - $|\mathcal{D}|=n+1$
> - Each number $m$ in $[n^2+n]$ has a unique representation $m\equiv d-d'\pmod{n^2+n+1}$ for $d,d'\in \mathcal{D}$. 

**Examples.**
- $\mathcal{D}_{2}=\{1,2,4\}$
- $\mathcal{D}_3=\{1,2,4,10\}$
- $\mathcal{D}_4=\{1,2,5,15,17\}$

> [!theorem]
> Let $\mathcal{D}$ be a different set of order $n\geqslant 2$. 
> Then the following is a projective plane of order $n$:
> - the points are $0,1,\cdots,n^2+n$;
> - the lines are $\mathcal{D}+i$ with $i\in\{0,\cdots,n^2+n\}$, where $\mathcal{D}+i=\{d+i:d\in \mathcal{D}\}$ module $n^2+n+1$.

 **Remark.** The projective plane induced from $\mathcal{D}_2$ is Fano plane. 

`\begin{proof}`
i) Let $x,x'$ be points. 
By definition of $\mathcal{D}$, there exist unique $d,d'\in \mathcal{D}$ such that $x-x'\equiv d-d'\pmod{n^2+n+1}$. 
Put $i=x-d$, then $i=x'-d'$ module $n^2+n+1$. 
Thus $\mathcal{D}+i$ is a line through $x$ and $x'$. 
Conversely, if $x,x'\in \mathcal{D}+i^*$, then $x=d_1+i^*$ and $x'=d_2+i^*$. 
It deduces that $x-x'=d_1-d_2\pmod{n^2+n+1}$, and so $d_1=d$, $d_2=d'$. 
Therefore, $i^*=i$ and the line through $x$ and $x'$ is unique. 

ii) Let $\mathcal{D}+i$ and $\mathcal{D}+j$ be distinct lines. 
Then $x\in (\mathcal{D}+i)\cap(\mathcal{D}+j)$ iff there exists $d,d'\in \mathcal{D}$ such that $x\equiv d+i\equiv d'+j\pmod{n^2+n+1}$. 
Then $d,d'$ are determined by $j-i$ and so $x$ is uniquely determined.
`\end{proof}`

# Ovals

> [!definition]
> An arc in a projective plane is a set of points such that no three points are collinear.


> [!lemma]
> Let $G$ be an arc of a projective plane of order $n$. Then $|G|\leqslant n+2$ and $|G|\leqslant n+1$ if $n$ is odd. 

`\begin{proof}`
Take $P\in G$, then there are $n+1$ lines through $P$ and each line has at most one point in $G$. 
Hence $|G|\leqslant 1+n+1=n+2$. 

If the equality holds, then no line intersects $G$ in $1$ point. 
Take point $Q\notin G$. 
Let $m$ denote number of secant lines through $Q$. 
Then $n+2=|G|=2m$. 
It is impossible for $n$ odd. 
`\end{proof}`

> [!definition]
> - An arc of size $n+1$ is called an oval. 
> - An arc of size $n+2$ is called hyperoval.
> - Conic is anything isomorphic to 
> 
> $$
> \begin{aligned}
> G&=\{\left\langle x,y,z\right\rangle :x^2=yz\}\\&=\{\left\langle (0,1,0)\right\rangle\}\cup\{\left\langle (t,t^2,1)\right\rangle:t\in\mathrm{GF}(q) \}.
> \end{aligned}
> $$
> 
> Remark that conics are ovals when $q$ is odd. 


> [!proposition]
> The set $\mathcal{O}_i=\{\left\langle (0,0,1)\right\rangle\}\cup\{\left\langle (1,t,t^{2^i})\right\rangle:t\in\mathrm{GF}(2^h) \}$ is an oval in $PG(2,2^h)$ iff $\gcd(i,h)=1$. 

`\begin{proof}`
Every line incident with $\left\langle (0,0,1)\right\rangle$ of the form $y=ax$ is incident with precisely one more point of $\mathcal{O}_i$, namely, $\left\langle (1,a,a^{2^i})\right\rangle$. 
The line $x=0$ is a tangent. 
The other lines are of the form $z=ax+by$. 
The line $z=ax+by$ is incident with $\left\langle (1,t,t^{2^i})\right\rangle$ iff $t^2=bt+a$. 
If $u^{2^i}=bu+a$ and $v^{2^i}=bv+a$, then $u^{2^i}-v^{2^i}=b(u-v)$, but also $u^{2^i}-v^{2^i}=(u-v)^{2^i}$. 
Thus, $b=(u-v)^{2^i-1}$. 

As $\gcd(i,h)=1$, there exists $m,n$ such that $m(2^i-1)+n(2^h-1)=1$. 
Hence $b^m=(u-v)^{1-n(2^h-1)}=u-v$. 
So $u,v$ determine $b$ and we do not have further solutions. 
`\end{proof}`

