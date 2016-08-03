-- useful queries to validate similarity scoring
--


select count(*) from similar;

select count(*) from similar where score < 0.99 ;

select score from similar where score < 0.99 order by score desc limit 10;

select d1.title, d2.title
  from document d1
  join similar s on d1.uid = s.uid_1
  join document d2 on s.uid_2 = d2.uid
 where s.score < 0.99
order by s.score desc
limit 10;

-- set to play with
select category, uid from document where category = 'bureaus' limit 5;

/* results holding bin



*/

-- query for similar documents
select d2.title, s.score
  from document d1
  join similar s on d1.uid = s.uid_1
  join document d2 on s.uid_2 = d2.uid
 where s.score < 0.99
   and d1.uid = ''
order by s.score desc
limit 10;