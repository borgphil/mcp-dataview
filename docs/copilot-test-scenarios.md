# Copilot Test Scenarios

Run each prompt through `validate_query` first, record the generated restricted SQL, then run it through `query` and compare the result with the expected behavior.

| Prompt | Required capability |
| --- | --- |
| Show me the first 20 customers. | `LIMIT` |
| Show me customers in the UK. | Equality |
| Show me active UK customers over 40. | `AND`, comparison |
| Show me customers in the UK or US. | `OR` |
| Show me active customers in the UK or US who are over 40. | Parentheses and mixed boolean logic |
| Find customers whose name starts with Smith. | `LIKE` |
| Show me customers in the UK, US or France. | `IN` |
| Show customers sorted by country ascending and name descending. | Multiple `ORDER BY` fields |
| Give me customers that invested in Product X. | Customers -> investments -> products |
| Show me the total investment for each customer. | `SUM`, `GROUP BY` |
| Show me the number of investors for each product. | `COUNT`, `GROUP BY` |
| Show me products with more than 100 investors. | `HAVING` |
| Show me the top 20 products by total investment, only above £1 million. | Multi-view aggregation and `HAVING` |
| Show me customers 201 to 300. | `LIMIT` and `OFFSET` |

The server must validate identifiers, relationship paths, grouping rules, complexity, and parameter binding independently of Copilot behavior.
