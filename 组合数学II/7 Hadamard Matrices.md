
# Hadamard Matrices

> [!definition]
> A Hadamard matrix of order $n$ is $(n\times n)$-matrix $H$ with entries $-1,1$ such that $HH^T=nI$. 

**Example.**
[![300](https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/HadamardConjectureMIT.png/250px-HadamardConjectureMIT.png)](https://en.wikipedia.org/wiki/File:HadamardConjectureMIT.png)

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



