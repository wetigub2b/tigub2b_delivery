if [ $1 = "" ];then
 msg="$1"
else
 msg=Update
fi
git add --all
git commit -m "$msg"
git push
