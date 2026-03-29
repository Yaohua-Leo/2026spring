
# Hadamard Matrices

> [!definition]
> A Hadamard matrix of order $n$ is $(n\times n)$-matrix $H$ with entries $-1,1$ such that $HH^T=nI$. 

**Example.**

![300](https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/HadamardConjectureMIT.png/250px-HadamardConjectureMIT.png)

**Two operations.** Let $H$ be a Hadamard matrix. Then
- Multiplying a row/column of $H$ by $-1$, results in a Hadamard matrix.
- Permuting rows/columns of $H$ results in a Hadamard matrix.

Hence, we can always get a form of $H$ like this 

$$
\begin{bmatrix}
1 & 1 & \cdots & 1 \\
1 &  \\
\vdots &  & * \\
1
\end{bmatrix}.
$$

> [!theorem]
> If $H$ is a Hadamard matrix of order $n$, then $n=1$, $n=2$, or $n\equiv 0\pmod 4$. ^09ce21

`\begin{proof}`
Let $n>2$. 
WLOG assume that first row $n$ are $1$'s. 
Then the second row: $n/2$ $1$'s and $n/2$ $-1$'s. 
It follows that $n\equiv 0\pmod 2$. 
Similarly compute the third row and get $n\equiv 0\pmod 4$. 
For more details, see [[A course in combinatorics - 2001 - van Lint, Wilson.pdf]], Theorem 18.1. 
`\end{proof}`

> [!conjecture] Hadamard Conjecture.
> The condition in [[#^09ce21]] is sufficient. 

Still open question. 
It has been verified $\leqslant 668,716$. 

> [!theorem] Hadamard, 1893
> $M=(m_{ij})\in \mathbb{C}^{n\times n}$, $|m_{ij}|\leqslant 1$, then $|\det(M)|\leqslant n^{n/2}$. The equality holds iff $MM^*=nI$. In that case, $|m_{ij}|=1$. 


> [!proposition] Sylvester's construction
> If $H$ is a Hadamard matrix, then $\begin{pmatrix} H & H\\ H & -H\end{pmatrix}$ is a Hadamard matrix.  ^jqjjg1

`\begin{proof}`
Easy. 
`\end{proof}`

Recall that for two matrices $A$ and $B$, $A\otimes B$ is defined [[6 Inner product & Schur's orthogonality relations#^9xanac|here]].

> [!theorem]
> If $H_m,H_n$ are Hadamard matrices of order $m,n$, respectively. Then $H_m\otimes H_n$ is a Hadamard matrix of order $mn$. 

`\begin{proof}`
Similar to [[#^jqjjg1]]. 
`\end{proof}`


> [!definition]
> A *conference matrix* $C$ of order $n$ is an $(n\times n)$-matrix with $0$'s on the diagonal, and $\pm 1$ everywhere else such that $C C^T=(n-1)I$. 

We have equivalence classes for conference matrices:
- multiplying row/column by $-1$
- permute row and column (at the same time)

> [!lemma]
> Let $C$ be a conference matrix of order $n>1$, then $2\mid n$. Furthermore, 
> - If $n\equiv 2\pmod 4$, then we can find an "equivalent" symmetric conference matrix ($C=C^T$). 
> - If $n\equiv 0\pmod 4$, then we can find an "equivalent" antisymmetric conference matrix $(C=-C^T)$. 

`\begin{proof}`
Similar to Hadamard matrices. 
`\end{proof}`


> [!theorem]
> If $C$ is an antisymmetric conference matrix, then $I+C$ is a Hadamard matrix. 

`\begin{proof}`
$(I+C)(I+C)^T=I+C+C^T+CC^T=I+C+(-C)+(n-1)I=nI$. 
`\end{proof}`


> [!theorem]
> If $C$ is a symmetric conference matrix, then $H=\begin{pmatrix} I+C & -I+C \\ -I+C & -I+C\end{pmatrix}$ is a Hadamard matrix. 

`\begin{proof}`
Easy. 
`\end{proof}`


> [!definition]
> Define $\chi:\mathrm{GF}(q)\to\{-1,0,1\}\subseteq \mathbb{C}$ as
> 
> $$\chi(x)=
> \begin{cases}
> 0 & \text{if }x=0,\\
> 1 & \text{if }x\text{ is square}, \\
> -1 & \text{if }x\text{ is nonsquare}.
> \end{cases}
> $$

> [!proposition]
> The followings hold. 
> - $\chi(x)\chi(y)=\chi(xy)$
> - $\sum_{x\in \mathrm{GF}(q)}=0$
> - $\sum_{b\in \mathrm{GF}(q)}\chi(b)\chi(b+c)=-1$ ^hx2ueq

`\begin{proof}`
i) and ii) are easy. 

For iii), note that 

$$
\sum_{b\in \mathrm{GF}(q)}\chi(b)\chi(b+c)=\sum_{b\in\mathrm{GF}(q)}\chi(b)\chi(b)\chi(1+cb^{-1})=\sum_{d\in\mathrm{GF}(q),d\neq 1}\chi(d)=-1.
$$

Now we finish the proof. 
`\end{proof}`


Write $\mathbb{F}_q=\{0,a_1,\cdots,a_{q-1}\}$. 
Define the $q\times q$ matrix $Q$ by $q_{ij}=\chi(a_i-a_j)$ for all $0\leqslant i,j\leqslant q$. 
Hence, if $q\equiv 1\pmod 4$, $Q$ is symmetric; if $q\equiv 3\pmod 4$, $Q$ is antisymmetric. 

Define a $(q+1)\times (q+1)$ matrix $C$ by 

$$
C=\begin{pmatrix}
0 & 1 & \cdots & 1 \\
\pm 1 \\
\vdots  &   & Q\\ 
\pm 1 
\end{pmatrix}
$$

such that $C$ is symmetric/antisymmetric. 

By [[#^hx2ueq]] ii) and iii), we have $QJ=JQ=0$ and $QQ^T=qI-J$. 
Hence $C$ is a conference matrix. 

> [!theorem] John Williamson, 1944
> Take matrices $A_1,A_2,A_3,A_4$ such that they are symmetric and commutative. 
> Define
> 
> $$
> H=
> \begin{pmatrix} 
A_1 & A_2 & A_3 & A_4\\ -A_2 & A_1 & -A_4 & A_3 \\ -A_3 & A_4 & A_1 & -A_2 \\ -A_4 & -A_3 & A_2 & A_1
\end{pmatrix}.
> $$
> 
> Then $HH^T=I_4\otimes(A_1^2+A_2^2+A_3^2+A_4^2)$. So $H$ is Hadamard if
> - $A_i$ entries in $\pm 1$;
> - $A_iA_j=A_jA_i$;
> - $A_1^2+A_2^2+A_3^2+A_4^2=4n I_n$. 

